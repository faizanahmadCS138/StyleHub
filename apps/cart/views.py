from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user
from rest_framework.permissions import AllowAny
from django.views.generic import TemplateView
from rest_framework.authentication import SessionAuthentication
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .cart_manager import StyleHubCartManager
from apps.catalog.models import Product

# @method_decorator(csrf_exempt, name='dispatch')
class CartAPIView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [AllowAny]

    """
    GET  -> Read current cart contents & total
    POST -> Add or Update item quantity
    DELETE -> Remove item from cart
    """

    def get(self, request):
        cart_mgr = StyleHubCartManager(request)
        return Response({
            'ok': True,
            'items': cart_mgr.get_items(),
            'summary': cart_mgr.get_summary()
        }, status=status.HTTP_200_OK)

    def post(self, request):
        
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        override_quantity = request.data.get('override_quantity', False)

        if not variant_id:
            return Response({'error': 'variant_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        print("Session auth keys:", dict(request.session.items()))
        print("get_user(request):", get_user(request))
        cart_mgr = StyleHubCartManager(request)
        cart_mgr.add(variant_id=variant_id, quantity=quantity, override_quantity=override_quantity)

        return Response({
            'ok': True,
            'message': 'Cart updated successfully.',
            'items': cart_mgr.get_items(),
            'summary': cart_mgr.get_summary()
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        variant_id = request.data.get('variant_id')
        if not variant_id:
            return Response({'error': 'variant_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        cart_mgr = StyleHubCartManager(request)
        cart_mgr.remove(variant_id=variant_id)

        return Response({
            'message': 'Item removed from cart.',
            'items': cart_mgr.get_items(),
            'summary': cart_mgr.get_summary()
        }, status=status.HTTP_200_OK)


class CartPageView(TemplateView):
    template_name = 'cart/cart.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    # Fetch featured or random products for recommendations
        context['related_products'] = Product.objects.filter(
        is_active=True
        ).order_by('?')[:10]
        return context