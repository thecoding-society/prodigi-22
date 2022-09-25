from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, Listing, Bid, Comment, Watchlist
from .forms import NewItem

def index(request):
    return render(request, "auctions/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.error(request, 'Invalid username and/or password.')
            return redirect('login')
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            messages.error(request, 'Passwords must match')
            return redirect('register')

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            messages.error(request, 'Username already taken.')
            return redirect('register')
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required
def new_listing(request):

    if request.method == 'POST':
        form = NewItem(request.POST)
        if form.is_valid():
            username = request.user.get_username()
            user = User.objects.get(username=username) 

            new = Listing(
                user = user,
                title = form.cleaned_data['title'],
                desc = form.cleaned_data['desc'],
                img = form.cleaned_data['img'],
                category = form.cleaned_data['category'],
                start_bid = form.cleaned_data['start_bid'],
            )
            new.save()

            messages.success(request, 'Added listing successfully.')
            return redirect('index')

        
        messages.error(request, 'Form not valid.')
        return redirect('newlisting')            

    form = NewItem()
    return render(request, "auctions/newlisting.html", {'form': form})
