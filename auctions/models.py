from pyexpat import model
from unicodedata import category
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Listing(models.Model):
    id = models.IntegerField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")
    title = models.CharField(max_length=50)
    desc = models.CharField(max_length=200, blank=True, null=True)
    img = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=50 ,blank=True, null=True)
    active_status = models.BooleanField(default=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="bidwinner")


class Bid(models.Model):
    id = models.IntegerField(primary_key=True)
    list_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="biddings")
    amount = models.IntegerField()
    winner = models.BooleanField(default=False)


class Comment(models.Model):
    id = models.IntegerField(primary_key=True)
    list_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="list_comments")
    user_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="user_comments")
    comment = models.CharField(max_length=200)

class Watchlist(models.Model):
    id = models.IntegerField(primary_key=True)
    list_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchlisted")
    user_id = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchlist")