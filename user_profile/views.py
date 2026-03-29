from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address

@login_required
def user_profile(request):
    return render(request, 'user_profile/profile.html')


@login_required
def profile_edit(request):
    user = request.user

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        phone = request.POST.get("phone")
        photo = request.FILES.get("photo")
        remove_photo = request.POST.get("remove_photo")

        # Split name
        if full_name:
            name_parts = full_name.split()
            user.first_name = name_parts[0]
            user.last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Phone
        user.phone_number = phone

        # Remove photo
        if remove_photo == "1":
            user.profile_image = None

        # Upload photo
        if photo:
            user.profile_image = photo

        user.save()

        return redirect('user_profile:user_profile')

    return render(request, 'user_profile/profile_edit.html')

@login_required
def manage_address(request):
    addresses = Address.objects.filter(user=request.user)

    return render(request, 'user_profile/manage_address.html', {
        'addresses': addresses
    })

@login_required
def add_address(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('mobile_number')
        address = request.POST.get('address')

        # 🔥 validation
        if not full_name or not phone or not address:
            messages.error(request, "Please fill all required fields")
            return redirect('user_profile:add_address')

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            district=request.POST.get('district'),
            state=request.POST.get('state'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pin_code'),
            landmark=request.POST.get('landmark'),
        )

        return redirect('user_profile:manage_address')

    return render(request, 'user_profile/add_address.html')

@login_required
def edit_address(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)

    if request.method == 'POST':
        address.full_name = request.POST.get('full_name')
        address.phone = request.POST.get('phone')
        address.address = request.POST.get('address')
        address.district = request.POST.get('district')
        address.state = request.POST.get('state')
        address.city = request.POST.get('city')
        address.pincode = request.POST.get('pincode')
        address.landmark = request.POST.get('landmark')
        address.save()

        return redirect('user_profile:manage_address')

    return render(request, 'user_profile/edit_address.html', {
        'address': address
    })

@login_required
def delete_address(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)

    if request.method == 'POST':
        address.delete()
        return redirect('user_profile:manage_address')

    return render(request, 'user_profile/delete_address.html', {
        'address': address
    })
