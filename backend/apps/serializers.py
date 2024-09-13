from rest_framework import serializers
from .models import Tender, Bid, BidVersion, TenderVersion, Review


class TenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tender
        fields = [
            'id',
            'name',
            'description',
            'service_type',
            'status',
            'organization',
            'creator_username',
            'created_at',
            'updated_at',
            'version'
        ]


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = [
            'id',
            'name',
            'description',
            'status',
            'tender',
            'organization',
            'creator_username',
            'created_at',
            'updated_at',
            'version',
            'votes_for'
        ]


class BidVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = BidVersion
        fields = [
            'id', 
            'bid_id', 
            'name', 
            'description', 
            'status', 
            'tender_id', 
            'organization_id', 
            'creator_username', 
            'created_at', 
            'updated_at', 
            'version', 
            'votes_for', 
        ]

class TenderVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenderVersion
        fields = [
            'id', 
            'tender_id', 
            'name', 
            'description', 
            'service_type', 
            'status', 
            'organization_id', 
            'creator_username', 
            'created_at', 
            'updated_at', 
            'version', 
        ]


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'bid', 'user', 'content', 'created_at']
