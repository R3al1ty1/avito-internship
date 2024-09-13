from django.db import models
import uuid


class Employee(models.Model):
    id = models.UUIDField(primary_key=True)
    username = models.CharField(unique=True, max_length=50)
    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'employee'


class Bid(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    tender = models.ForeignKey('Tender', models.DO_NOTHING, blank=True, null=True)
    organization = models.ForeignKey('Organization', models.DO_NOTHING, blank=True, null=True)
    creator_username = models.ForeignKey('Employee', models.DO_NOTHING, db_column='creator_username', to_field='username', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    version = models.IntegerField()
    votes_for = models.IntegerField()
    voters = models.ManyToManyField(Employee, related_name="voted_bids", blank=True)

    class Meta:
        managed = False
        db_table = 'bid'


class Organization(models.Model):
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organization'


class OrganizationResponsible(models.Model):
    id = models.UUIDField(primary_key=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(Employee, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organization_responsible'


class Tender(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    service_type = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    creator_username = models.ForeignKey(Employee, models.DO_NOTHING, db_column='creator_username', to_field='username', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    version = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tender'


class BidVersion(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    tender = models.ForeignKey('Tender', models.DO_NOTHING, blank=True, null=True)
    organization = models.ForeignKey('Organization', models.DO_NOTHING, blank=True, null=True)
    creator_username = models.ForeignKey('Employee', models.DO_NOTHING, db_column='creator_username', to_field='username', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    votes_for = models.IntegerField(blank=True, null=True)
    bid_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'bid_version'


class TenderVersion(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    service_type = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    organization = models.ForeignKey(Organization, models.DO_NOTHING, blank=True, null=True)
    creator_username = models.ForeignKey(Employee, models.DO_NOTHING, db_column='creator_username', to_field='username', blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    version = models.IntegerField(blank=True, null=True)
    tender_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tender_version'


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
    user = models.ForeignKey(Employee, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'review'
