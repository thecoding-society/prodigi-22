from multiprocessing import context
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, Listing, Bid, Comment, Watchlist
from .forms import NewItem
from commerce.settings import LOGIN_REDIRECT_URL
from django.db.models import Max



def index(request):
    if request.user.is_authenticated:
        # adding listing to watchlist
        if request.method == 'POST':
            list_id = request.POST.get('list_id')
            if list_id == None:
                messages.error(request, 'Something went wrong, try again.')
                return redirect('index')
            uname = request.user.get_username()

            user= User.objects.get(username=uname)
            try:
                listing = Listing.objects.get(pk=list_id)
            except:
                messages.error(request, 'Something went wrong, try again.')
                return redirect('listing', list_id=list_id)
        
            # check if listing already in watchlist
            watchlistings = user.watchlist.all()

            for watchlisting in watchlistings:
                if int(watchlisting.list_id.id) == int(list_id):
                    messages.error(request, 'Listing already watchlisted.')
                    return redirect('index')

            
            # creating watchlist
            watchlisting = Watchlist(
                user_id=user,
                list_id=listing,
            )
            watchlisting.save()
            messages.success(request, 'Listing watchlisted.')
            return redirect('index')

    # list the active listing in index
    listings = Listing.objects.filter(active_status=True)

    # getting category
    for list in listings:
        list.category = list.get_category_display()
        
        # getting highest bid
        highest_amount_dict = list.bids.aggregate(Max('amount'))
        highest_amount = highest_amount_dict['amount__max']
        if highest_amount:
            list.bid = list.bids.get(amount=highest_amount)
    context = {
        'listings':listings
    }
    return render(request, "auctions/index.html", context)


def not_found(request):
    return render(request, "auctions/notfound.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        print(username, password, user)
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


@login_required(login_url=LOGIN_REDIRECT_URL)
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
    context= {
        'form': NewItem()
    }
    return render(request, "auctions/newlisting.html", context)


@login_required(login_url=LOGIN_REDIRECT_URL)
def listing(request, list_id):
    
    if request.user.is_authenticated:
        uname = request.user.get_username()
        user= User.objects.get(username=uname)
        if request.method == 'POST':

            # adding listing to watchlist
            if 'watchlist' in request.POST:
                if list_id == None:
                    messages.error(request, 'Something went wrong, try again.')
                    return redirect('listing', list_id=list_id)
                
                try:
                    listing = Listing.objects.get(pk=list_id)
                except:
                    messages.error(request, 'Something went wrong, try again.')
                    return redirect('listing', list_id=list_id)
                # check if listing already in watchlist
                watchlistings = user.watchlist.all()

                for watchlisting in watchlistings:
                    if int(watchlisting.list_id.id) == int(list_id):
                        messages.error(request, 'Listing already watchlisted.')
                        return redirect('listing', list_id=list_id)

                
                # creating watchlist
                watchlisting = Watchlist(
                    user_id=user,
                    list_id=listing,
                )
                watchlisting.save()
                messages.success(request, 'Listing watchlisted.')
                return redirect('listing', list_id=list_id)

            elif 'bid' in request.POST:
                # get bid
                bid_amount = request.POST.get('bid_amount')
                if bid_amount == None:
                    messages.error(request, 'Enter valid bid.')
                    return redirect('listing', list_id=list_id)
                
                listing= Listing.objects.get(pk=list_id)
                
                # getting highest bid
                highest_amount_dict = listing.bids.aggregate(Max('amount'))
                highest_amount = highest_amount_dict['amount__max']


                # check valid bid
                if highest_amount:
                    if int(highest_amount)>=int(bid_amount):
                        messages.error(request, 'Bid must be higher than current bid.')
                        return redirect('listing', list_id=list_id)
                else:
                    if int(listing.start_bid)>int(bid_amount):
                        messages.error(request, 'Bid must be higher or equal to starting bid.')
                        return redirect('listing', list_id=list_id)

                # place bid
                new_bid = Bid(
                    list_id=listing,
                    user_id=user,
                    amount=bid_amount,
                )
                new_bid.save()

                messages.success(request, 'Bid placed.')
                return redirect('listing', list_id=list_id)

            elif 'close' in request.POST:
                listing= Listing.objects.get(pk=list_id)
                if user.id != listing.user.id:
                    messages.error(request, 'Only owners can close the listing.')
                    return redirect('listing', list_id=list_id)

                # getting highest bid
                highest_amount_dict = listing.bids.aggregate(Max('amount'))
                highest_amount = highest_amount_dict['amount__max']
                if highest_amount:
                    highest_bid = listing.bids.get(amount=highest_amount)
                
                listing.active_status= False
                listing.winner = highest_bid.user_id
                listing.save()
                messages.success(request, 'Listing closed.')
                return redirect('listing', list_id=list_id)

            elif 'comment' in request.POST:
                comment = request.POST.get('usercomment')
                listing= Listing.objects.get(pk=list_id)
                new_comment = Comment(
                    list_id= listing,
                    user_id = user,
                    comment=comment
                )
                new_comment.save()
                messages.success(request, 'Comment added')
                return redirect('listing', list_id=list_id)



        # get listing
        try:
            listing = Listing.objects.get(pk=list_id)
        except:
            return redirect('not_found')


        # getting human readable category
        listing.category = listing.get_category_display()
        
        # getting highest bid
        highest_amount_dict = listing.bids.aggregate(Max('amount'))
        highest_amount = highest_amount_dict['amount__max']
        if highest_amount:
            listing.bid = listing.bids.get(amount=highest_amount)
        
        
        # getting count of bids placed
        count = listing.bids.count()

        # get comments
        comments= listing.list_comments.all()

        context={
            'listing':listing,
            'count': count,
            'user': user,
            'comments': comments,
        }
        return render(request, "auctions/listing.html", context)


@login_required(login_url=LOGIN_REDIRECT_URL)
def watchlist(request):
    username = request.user.get_username()
    user = User.objects.get(username=username) 

    listings=user.watchlist.all()
    for listing in listings:
         # getting highest bid
        highest_amount_dict = listing.list_id.bids.aggregate(Max('amount'))
        highest_amount = highest_amount_dict['amount__max']
        if highest_amount:
            listing.list_id.bid = listing.list_id.bids.get(amount=highest_amount)

    context= {
        'listings': listings
    }

    return render(request, "auctions/watchlist.html", context)
