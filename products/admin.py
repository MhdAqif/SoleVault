from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, Size, ProductVariant

admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(Size)
admin.site.register(ProductVariant)