from django.db import models


class Category(models.Model):
    GENDER_CHOICES = [
        ('men',   'Men'),
        ('women', 'Women'),
    ]
    name   = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='men')
    slug   = models.SlugField(unique=True)
    image  = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    GENDER_CHOICES = [
        ('men',   'Men'),
        ('women', 'Women'),
        ('unisex','Unisex'),
    ]

    OCCASION_CHOICES = [
        ('casual', 'Casual'),
        ('sports', 'Sports'),
        ('formal', 'Formal'),
    ]
    MATERIAL_CHOICES = [
        ('leather', 'Leather'),
        ('suede',   'Suede'),
        ('mesh',    'Mesh'),
        ('canvas',  'Canvas'),
    ]

    name           = models.CharField(max_length=200)
    slug           = models.SlugField(unique=True)
    brand          = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    category       = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    gender         = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    occasion       = models.CharField(max_length=20, choices=OCCASION_CHOICES, default='casual')
    material       = models.CharField(max_length=20, choices=MATERIAL_CHOICES, default='mesh')
    description    = models.TextField(blank=True)
    price          = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image          = models.ImageField(upload_to='products/')
    is_new         = models.BooleanField(default=False)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def discount(self):
        """Return discount percentage if original price exists."""
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return None

    @property
    def active_offer_percentage(self):
        """Returns the highest active offer discount percentage."""
        discount_pct = 0
        # Check product offer
        if hasattr(self, 'product_offer') and self.product_offer.is_active:
            discount_pct = max(discount_pct, self.product_offer.discount_percentage)
        # Check category offer
        if self.category and hasattr(self.category, 'category_offer') and self.category.category_offer.is_active:
            discount_pct = max(discount_pct, self.category.category_offer.discount_percentage)
        return discount_pct

    @property
    def offer_price(self):
        """Returns the selling price after applying the highest active offer discount between ProductOffer and CategoryOffer."""
        discount_pct = self.active_offer_percentage
        if discount_pct > 0:
            import decimal
            discount_multiplier = decimal.Decimal(str(100 - discount_pct)) / decimal.Decimal('100.00')
            return (self.price * discount_multiplier).quantize(decimal.Decimal('0.01'))
        return self.price

    @property
    def is_in_stock(self):
        """Return True if at least one variant is in stock."""
        return self.variants.filter(stock__gt=0).exists()


class ProductImage(models.Model):
    """Additional images for a product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image   = models.ImageField(upload_to='products/gallery/')
    alt     = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.product.name} – image'


class Size(models.Model):
    name = models.CharField(max_length=10)   # e.g. "7", "8.5", "UK 9"

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """Stock per product + size + colour."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size    = models.ForeignKey(Size, on_delete=models.CASCADE)
    color   = models.CharField(max_length=50, blank=True)
    stock   = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.product.name} | {self.size} | {self.color}'


class ProductOffer(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='product_offer')
    discount_percentage = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer: {self.product.name} – {self.discount_percentage}%"


class CategoryOffer(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name='category_offer')
    discount_percentage = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Offer: {self.category.name} – {self.discount_percentage}%"