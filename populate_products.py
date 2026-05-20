import os
import django
import random

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solevault.settings')
django.setup()

from products.models import Brand, Category, Size, Product, ProductVariant

def populate():
    print("Starting population script...")

    # 1. Create Sizes
    size_names = ['5', '5.5', '6', '6.5', '7', '7.5', '8', '8.5', '9', '9.5', '10', '10.5', '11', '12', '13']
    for sn in size_names:
        Size.objects.get_or_create(name=sn)
    print(f"Created/Verified {len(size_names)} sizes.")

    # 2. Get Brands
    nike = Brand.objects.get(name='Nike')
    adidas = Brand.objects.get(name='Adidas')
    puma = Brand.objects.get(name='Puma')
    nb = Brand.objects.get(name='New Balance')

    # 3. Get Categories
    cat_men_run = Category.objects.get(slug='running-men')
    cat_men_life = Category.objects.get(slug='lifestyle-men')
    cat_women_run = Category.objects.get(slug='running-women')
    cat_women_life = Category.objects.get(slug='lifestyle-women')

    # Helper for variants
    all_sizes = list(Size.objects.all())
    colors = ['Black', 'White', 'Navy', 'Grey', 'Royal Blue', 'Red', 'Sand', 'Sage']

    def add_product(name, brand, category, price, slug, image_path, description, occasion, material):
        product, created = Product.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'brand': brand,
                'category': category,
                'price': price,
                'image': image_path,
                'description': description,
                'occasion': occasion,
                'material': material,
                'is_active': True,
                'is_new': True
            }
        )
        if created:
            print(f"Created product: {name}")
            # Add 5 random variants
            selected_sizes = random.sample(all_sizes, 5)
            for s in selected_sizes:
                ProductVariant.objects.create(
                    product=product,
                    size=s,
                    color=random.choice(colors),
                    stock=random.randint(10, 50)
                )
        else:
            print(f"Product already exists: {name}")

    # 4. Add Products
    # Nike
    add_product("Nike Air Pegasus 40", nike, cat_men_run, 11495, "nike-pegasus-40", "products/nike-pegasus.jpg", 
                "A springy ride for every run, the Pegasus's familiar, just-for-you feel returns to help you accomplish your goals.", "sports", "mesh")
    add_product("Nike Air Force 1 '07", nike, cat_men_life, 7495, "nike-af1-07", "products/nike-pegasus.jpg", 
                "The radiance lives on in the Nike Air Force 1 '07, the b-ball icon that puts a fresh spin on what you know best.", "casual", "leather")
    add_product("Nike Zoom Fly 5", nike, cat_women_run, 14995, "nike-zoom-fly-5", "products/nike-pegasus.jpg", 
                "Bridge the gap between your weekend training run and race day in a durable design.", "sports", "mesh")

    # Adidas
    add_product("Adidas Ultraboost Light", adidas, cat_men_run, 18999, "adidas-ultraboost-light", "products/cropped_1776165091380.jpg", 
                "Experience epic energy with the new Ultraboost Light, our lightest Ultraboost ever.", "sports", "mesh")
    add_product("Adidas Stan Smith Classic", adidas, cat_women_life, 8999, "adidas-stan-smith", "products/cropped_1776165091380.jpg", 
                "Timeless appeal. Effortless style. Everyday versatility. For over 50 years, Adidas Stan Smith shoes have continued to hold their ground.", "casual", "leather")

    # Puma
    add_product("Puma RS-X Efekt", puma, cat_men_life, 9999, "puma-rs-x-efekt", "products/puma-rsx.jpg", 
                "The RS-X is back. The future-retro silhouette of this sneaker returns with a progressive aesthetic and angular details.", "casual", "suede")
    add_product("Puma Velocity Nitro 2", puma, cat_women_run, 10999, "puma-velocity-nitro-2", "products/puma-rsx.jpg", 
                "An all-in-one neutral running shoe for any distance, the Velocity Nitro 2 is a lightweight and sleek update to the Run PUMA roster.", "sports", "mesh")

    # New Balance
    add_product("New Balance 550", nb, cat_men_life, 11999, "nb-550-retro", "products/nb-550.jpg", 
                "The original 550 debuted in 1989 and made its mark on basketball courts from coast to coast.", "casual", "leather")
    add_product("New Balance 574 Core", nb, cat_women_life, 7999, "nb-574-core", "products/nb-550.jpg", 
                "The most New Balance shoe ever says it all, right? No, actually. The 574 might be our unlikeliest icon.", "casual", "suede")

    print("Population complete!")

if __name__ == '__main__':
    populate()
