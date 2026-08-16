"""
virtual_tryon/services.py

Virtual Try-On service using the hosted IDM-VTON Hugging Face Space.

Product images are stored locally in Django MEDIA_ROOT.
The local product image is passed directly to gradio_client, which uploads
it temporarily to the Hugging Face Space.

No try-on images are stored in the database or permanent media storage.
"""

import base64
import logging
import os
import tempfile
from concurrent.futures import TimeoutError as FuturesTimeoutError

from django.conf import settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

HF_SPACE_ID = getattr(
    settings,
    "VTON_HF_SPACE",
    "zhengchong/CatVTON",
)

HF_TOKEN = getattr(
    settings,
    "HF_TOKEN",
    "",
) or None

VTON_TIMEOUT_SECONDS = getattr(
    settings,
    "VTON_TIMEOUT_SECONDS",
    180,
)


class VirtualTryOnError(Exception):
    """
    User-safe exception for Virtual Try-On failures.
    """

    pass


# ──────────────────────────────────────────────────────────────────────────────
# GARMENT CATEGORY
# ──────────────────────────────────────────────────────────────────────────────

def get_garment_category(product):
    """
    Determine the garment category expected by IDM-VTON.

    Returns:

        upper_body
        lower_body
        dresses
    """

    category_name = (
        product.category.name
        if product.category
        else ""
    ).lower()

    parent_name = (
        product.category.parent.name
        if product.category and product.category.parent
        else ""
    ).lower()

    combined = f"{parent_name} {category_name}"

    # Dresses / one-piece garments
    if any(
        word in combined
        for word in [
            "dress",
            "gown",
            "jumpsuit",
            "romper",
        ]
    ):
        return "dresses"

    # Lower-body garments
    if any(
        word in combined
        for word in [
            "jean",
            "trouser",
            "pant",
            "short",
            "skirt",
            "bottom",
        ]
    ):
        return "lower_body"

    # Everything else is treated as upper body
    return "upper_body"


# ──────────────────────────────────────────────────────────────────────────────
# GARMENT DESCRIPTION
# ──────────────────────────────────────────────────────────────────────────────

def _build_garment_description(product):
    """
    Build the text description sent to IDM-VTON.
    """

    category = get_garment_category(product)

    label = {
        "upper_body": "top",
        "lower_body": "bottoms",
        "dresses": "dress",
    }[category]

    brand = getattr(product, "brand", None) or "StyleHub"

    product_name = getattr(product, "name", None) or "garment"

    return f"{brand} {product_name} ({label})"


# ──────────────────────────────────────────────────────────────────────────────
# LOCAL PRODUCT IMAGE
# ──────────────────────────────────────────────────────────────────────────────

def _get_local_garment_path(primary_image):
    """
    Convert the ProductImage ImageField name into an actual local filesystem
    path.

    Example:

        image.name:
            products/STRAIGHT_FIIT_JEANS.png

        MEDIA_ROOT:
            D:/DJANGO/Ecommerce/media

        Result:
            D:/DJANGO/Ecommerce/media/products/STRAIGHT_FIIT_JEANS.png
    """

    if not primary_image or not primary_image.image:
        raise VirtualTryOnError(
            "This product doesn't have an image available for try-on."
        )

    image_name = primary_image.image.name

    if not image_name:
        raise VirtualTryOnError(
            "This product doesn't have an image available for try-on."
        )

    # 1. Try standard django file path if storage supports it and file exists
    try:
        if hasattr(primary_image.image, "path") and os.path.isfile(primary_image.image.path):
            return os.path.abspath(primary_image.image.path)
    except Exception:
        pass

    # 2. Strip leading slashes and redundant 'media/' prefix if stored with it
    clean_name = image_name.lstrip('/\\')
    if clean_name.startswith('media/') or clean_name.startswith('media\\'):
        clean_name = clean_name[6:]

    local_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, clean_name))

    if os.path.isfile(local_path):
        return local_path

    # 3. Fallback: try matching common image extensions if file lacks extension
    base, ext = os.path.splitext(local_path)
    if not ext:
        for try_ext in ['.png', '.jpg', '.jpeg', '.webp']:
            if os.path.isfile(base + try_ext):
                return base + try_ext

    logger.error(
        "Product image does not exist locally: %s (original name: %s)",
        local_path,
        image_name,
    )

    raise VirtualTryOnError(
        "The product image could not be found. Please try another product."
    )



# ──────────────────────────────────────────────────────────────────────────────
# GENERATE TRY-ON
# ──────────────────────────────────────────────────────────────────────────────

def generate_tryon_image(
    person_image_field,
    primary_image,
    product,
):
    """
    Generate a virtual try-on image using IDM-VTON.

    Parameters
    ----------
    person_image_field:
        UploadedFile containing the user's selfie.

    primary_image:
        StyleHub ProductImage instance.

    product:
        StyleHub Product instance.

    Returns
    -------
    str
        Base64 PNG data URI.

    Important:
        Nothing is saved to the database.
        Nothing is permanently saved to MEDIA_ROOT.
    """

    try:
        from gradio_client import Client, handle_file

    except ImportError:

        logger.exception(
            "gradio_client is not installed."
        )

        raise VirtualTryOnError(
            "Virtual try-on is temporarily unavailable. "
            "Please try again later."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # GET LOCAL GARMENT IMAGE
    # ──────────────────────────────────────────────────────────────────────────

    garment_path = _get_local_garment_path(primary_image)

    # Temporary selfie file
    temp_person_path = None

    # Generated IDM-VTON output
    output_path = None

    # Masked image returned by IDM-VTON
    masked_output_path = None

    try:

        # ──────────────────────────────────────────────────────────────────────
        # SAVE USER SELFIE TO TEMP FILE
        # ──────────────────────────────────────────────────────────────────────

        suffix = (
            os.path.splitext(person_image_field.name)[1]
            or ".jpg"
        )

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:

            for chunk in person_image_field.chunks():
                temp_file.write(chunk)

            temp_person_path = temp_file.name

        logger.info(
            "Starting IDM-VTON for product %s",
            product.id,
        )

        # ──────────────────────────────────────────────────────────────────────
        # CONNECT TO HUGGING FACE
        # ──────────────────────────────────────────────────────────────────────

        #
        # IMPORTANT:
        #
        # Your installed gradio_client 2.6.0 does NOT support:
        #
        #     Client(..., hf_token=...)
        #
        # Therefore we don't pass hf_token to Client().
        #
        # IDM-VTON currently loads without it in your testing.
        #

        client = Client(HF_SPACE_ID)

        category = get_garment_category(product)
        garment_description = _build_garment_description(product)

        logger.info(
            "Sending person image and garment image to %s (category: %s)",
            HF_SPACE_ID,
            category,
        )

        # ──────────────────────────────────────────────────────────────────────
        # CALL VIRTUAL TRY-ON SPACE
        # ──────────────────────────────────────────────────────────────────────

        cloth_type_map = {
            "upper_body": "upper",
            "lower_body": "lower",
            "dresses": "overall",
        }
        cloth_type = cloth_type_map.get(category, "upper")

        if "catvton" in HF_SPACE_ID.lower():
            result = client.predict(
                person_image={
                    "background": handle_file(temp_person_path),
                    "layers": [],
                    "composite": None,
                },
                cloth_image=handle_file(garment_path),
                cloth_type=cloth_type,
                num_inference_steps=30,
                guidance_scale=2.5,
                seed=42,
                show_type="result only",
                api_name="/submit_function",
            )
        else:
            result = client.predict(
                {
                    "background": handle_file(temp_person_path),
                    "layers": [],
                    "composite": None,
                },
                garm_img=handle_file(garment_path),
                garment_des=garment_description,
                is_checked=True,
                is_checked_crop=False,
                denoise_steps=30,
                seed=42,
                api_name="/tryon",
            )


        # ──────────────────────────────────────────────────────────────────────
        # READ RESULT
        # ──────────────────────────────────────────────────────────────────────

        if not result:
            raise VirtualTryOnError(
                "IDM-VTON did not return an image."
            )

        if not isinstance(result, (list, tuple)):
            raise VirtualTryOnError(
                "Unexpected response from the Virtual Try-On service."
            )

        if len(result) < 1:
            raise VirtualTryOnError(
                "No try-on image was returned."
            )

        generated = result[0]

        # Depending on gradio_client version, this may be:
        #
        #   string path
        #
        # or:
        #
        #   {"path": "..."}
        #

        if isinstance(generated, dict):

            output_path = generated.get("path")

        else:

            output_path = generated

        # Masked image is result[1]
        if len(result) > 1:

            masked = result[1]

            if isinstance(masked, dict):

                masked_output_path = masked.get("path")

            else:

                masked_output_path = masked

        if not output_path:

            raise VirtualTryOnError(
                "IDM-VTON did not return a generated image."
            )

        if not os.path.isfile(output_path):

            logger.error(
                "IDM-VTON output does not exist: %s",
                output_path,
            )

            raise VirtualTryOnError(
                "Unable to generate your try-on right now."
            )

        # ──────────────────────────────────────────────────────────────────────
        # READ GENERATED IMAGE
        # ──────────────────────────────────────────────────────────────────────

        with open(output_path, "rb") as image_file:

            image_bytes = image_file.read()

        if not image_bytes:

            raise VirtualTryOnError(
                "The generated image was empty."
            )

        # Convert to base64 so we can send it directly to the browser.
        encoded = base64.b64encode(
            image_bytes
        ).decode("ascii")

        logger.info(
            "IDM-VTON successfully generated image for product %s",
            product.id,
        )

        return f"data:image/png;base64,{encoded}"

    # ──────────────────────────────────────────────────────────────────────────
    # KNOWN ERRORS
    # ──────────────────────────────────────────────────────────────────────────

    except VirtualTryOnError:
        raise

    except FuturesTimeoutError:

        logger.warning(
            "IDM-VTON timed out for product %s",
            product.id,
        )

        raise VirtualTryOnError(
            "This is taking longer than expected. "
            "Please try again in a moment."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # EVERYTHING ELSE
    # ──────────────────────────────────────────────────────────────────────────

    except Exception as exc:

        logger.error(
            "Virtual try-on generation failed for product %s: %s",
            product.id,
            exc,
            exc_info=True,
        )

        raise VirtualTryOnError(
            "Unable to generate your try-on right now. "
            "Please try again."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # CLEANUP
    # ──────────────────────────────────────────────────────────────────────────

    finally:

        # Delete the temporary user selfie.
        if (
            temp_person_path
            and os.path.exists(temp_person_path)
        ):

            try:

                os.remove(temp_person_path)

            except OSError:

                logger.warning(
                    "Could not delete temporary person image: %s",
                    temp_person_path,
                )

        # Delete generated output downloaded by gradio_client.
        if (
            output_path
            and os.path.exists(output_path)
        ):

            try:

                os.remove(output_path)

            except OSError:

                logger.warning(
                    "Could not delete generated output: %s",
                    output_path,
                )

        # Delete masked output downloaded by gradio_client.
        if (
            masked_output_path
            and os.path.exists(masked_output_path)
        ):

            try:

                os.remove(masked_output_path)

            except OSError:

                logger.warning(
                    "Could not delete masked output: %s",
                    masked_output_path,
                )