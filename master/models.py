#!/usr/bin/python
# -*- coding: utf-8 -*-
"""The Django Models Page for master app"""

import datetime

from django.contrib.gis.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from colorfield.fields import ColorField
from component.models import Component
from django.contrib.contenttypes.fields import GenericRelation

FACTSHEET_PHOTO="factsheet/"
SHELTER_PHOTO="ShelterPhotos/"
DRAINAGE_PHOTO="ShelterPhotos/FactsheetPhotos/"

class CityReference(models.Model):
    """Worldwide City Database"""
    city_name = models.CharField(max_length=2048)
    city_code = models.CharField(max_length=2048)
    district_name = models.CharField(max_length=2048)
    district_code = models.CharField(max_length=2048)
    state_name = models.CharField(max_length=2048)
    state_code = models.CharField(max_length=2048)

    def __str__(self):
        """Returns string representation of object"""
        return str(self.city_name)

class City(models.Model):
    """Shelter City Database"""
    name = models.ForeignKey(CityReference, on_delete=models.CASCADE)
    city_code = models.CharField(max_length=2048)
    state_name = models.CharField(max_length=2048)
    state_code = models.CharField(max_length=2048)
    district_name = models.CharField(max_length=2048)
    district_code = models.CharField(max_length=2048)
    shape = models.PolygonField(srid=4326)
    border_color = ColorField(default='#94BBFF')
    background_color = ColorField(default='#94BBFF')
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(default=datetime.datetime.now)

    components = GenericRelation(Component, related_query_name='component_city',object_id_field="object_id") #Fields for reverse relationship

    def __str__(self):
        """Returns string representation of object"""
        return str(self.name.city_name)

    class Meta:
        """Metadata for class City"""
        verbose_name = 'City'
        verbose_name_plural = 'Cities'

SURVEYTYPE_CHOICES = (('Slum Level', 'Slum Level'),
                      ('Household Level', 'Household Level'),
                      ('Household Member Level', 'Household Member Level'),
                      ('Family Factsheet', 'Family Factsheet'))

class Survey(models.Model):
    """Shelter Survey Database"""
    name = models.CharField(max_length=2048)
    description = models.CharField(max_length=2048)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    survey_type = models.CharField(max_length=2048,
                                   choices=SURVEYTYPE_CHOICES)
    analysis_threshold = models.IntegerField()
    kobotool_survey_id = models.CharField(max_length=2048)
    kobotool_survey_url = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        """Returns string representation of object"""
        return self.name

    class Meta:
        """Metadata for class Survey"""
        verbose_name = 'Survey'
        verbose_name_plural = 'Surveys'

class AdministrativeWard(models.Model):
    """Administrative Ward Database"""
    city = models.ForeignKey(City,related_name='admin_ward', on_delete=models.CASCADE)
    name = models.CharField(max_length=2048, default="")
    shape = models.PolygonField(srid=4326, default="")
    ward_no = models.CharField(max_length=2048, default="")
    description = models.TextField(max_length=2048,blank=True,null=True)
    office_address = models.CharField(max_length=2048,blank=True,null=True)
    border_color = ColorField(default='#BFFFD0')
    background_color = ColorField(default='#BFFFD0')

    def __str__(self):
        """Returns string representation of object"""
        return self.name

    class Meta:
        """Metadata for class Administrative Ward"""
        verbose_name = 'Administrative Ward'
        verbose_name_plural = 'Administrative Wards'


class ElectoralWard(models.Model):
    """Electoral Ward Database"""
    administrative_ward = models.ForeignKey(AdministrativeWard,related_name='electoral_ward',blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=2048, default="")
    shape = models.PolygonField(srid=4326, default="")
    ward_no = models.CharField(max_length=2048, default="", null=True, blank=True)
    ward_code = models.TextField(max_length=2048, default="", null=True, blank=True)
    extra_info = models.CharField(max_length=2048,blank=True,null=True)
    border_color = ColorField(default='#FFEFA1')
    background_color = ColorField(default='#FFEFA1')

    def __str__(self):
        """Returns string representation of object"""
        return self.name

    class Meta:
        """Metadata for class ElectoralWard"""
        verbose_name = 'Electoral Ward'
        verbose_name_plural = 'Electoral Wards'

ODF_CHOICES =(('',''), ('OD', 'OD'), ('ODF','ODF'),('ODF+','ODF+'),('ODF++','ODF++'))

class Slum(models.Model):
    """Slum Database"""
    electoral_ward = models.ForeignKey(ElectoralWard,related_name='slum_name',blank=True, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=2048)
    shape = models.PolygonField(srid=4326)
    description = models.TextField(max_length=2048,blank=True,null=True)
    shelter_slum_code = models.CharField(max_length=2048,blank=True,null=True)
    factsheet = models.FileField(upload_to=FACTSHEET_PHOTO ,blank=True,null=True)
    photo = models.ImageField(upload_to=FACTSHEET_PHOTO,blank=True, null=True)
    associated_with_SA = models.BooleanField(default=False)
    odf_status = models.CharField(max_length=2048,choices=ODF_CHOICES,default=ODF_CHOICES)
    status = models.BooleanField(default=False)

    components = GenericRelation(Component, related_query_name='component_slum',object_id_field="object_id")#Fields for reverse relationship

    def has_permission(self, user):
        if user.is_superuser:
            return True
        group_perm = user.groups.values_list('name', flat=True)
        group_perm = map(lambda x:x.split(':')[-1].strip(), group_perm)
        if self.electoral_ward.administrative_ward.city.name.city_name.strip() in group_perm:
            return True
        return False

    def __str__(self):
        """Returns string representation of object"""
        return str(self.name)

    class Meta:
        """Metadata for class Slum"""
        verbose_name = 'Slum'
        verbose_name_plural = 'Slums'
        ordering = ['name']

class WardOfficeContact(models.Model):
    """Ward Office Contact Database"""
    administrative_ward = models.ForeignKey(AdministrativeWard, on_delete=models.CASCADE)
    title = models.CharField(max_length=2048)
    name = models.CharField(max_length=2048)
    address_info = models.CharField(max_length=2048, default="")
    telephone = models.CharField(max_length=2048,blank=True,null=True)

    def __str__(self):
        """Returns string representation of object"""
        return self.name

    class Meta:
        """Metadata for WardOfficeContact"""
        verbose_name = 'Ward Officer Contact'
        verbose_name_plural = 'Ward Officer Contacts'


class ElectedRepresentative(models.Model):
    """Elected Reresentative Database"""
    electoral_ward = models.ForeignKey(ElectoralWard, on_delete=models.CASCADE)
    name = models.CharField(max_length=2048)
    tel_nos = models.CharField(max_length=2048)
    address = models.CharField(max_length=2048)
    post_code = models.CharField(max_length=2048)
    additional_info = models.CharField(max_length=2048,blank=True,null=True)
    elected_rep_Party = models.CharField(max_length=2048)

    def __str__(self):
        """Returns string representation of object"""
        return self.name

    class Meta:
        """Metadata for class ElectedRepresentative"""
        verbose_name = 'Elected Representative'
        verbose_name_plural = 'Elected Representatives'


class ShapeCode(models.Model):
    """Shape Code Database"""
    code = models.CharField(max_length=2048)
    description = models.CharField(max_length=2048)

    class Meta:
        """Metadata for class ShapeCode"""
        verbose_name = 'Shape Code'
        verbose_name_plural = 'Shape Codes'


class DrawableComponent(models.Model):
    """Drawable Component Database"""
    name = models.CharField(max_length=2048)
    color = models.CharField(max_length=2048)
    extra = models.CharField(max_length=2048)
    maker_icon = models.CharField(max_length=2048)
    shape_code = models.ForeignKey(ShapeCode, on_delete=models.CASCADE)

    def __str__(self):
        """Returns string representation of object"""
        return self.name

    class Meta:
        """Metadata for class Drawable Component"""
        verbose_name = 'Drawable Component'
        verbose_name_plural = 'Drawable Components'


class PlottedShape(models.Model):
    """Plotted Shape Database"""
    slum = models.CharField(max_length=2048)
    name = models.CharField(max_length=2048)
    lat_long = models.CharField(max_length=2048)
    drawable_component = models.ForeignKey(DrawableComponent, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created_on = models.DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        """Returns string representation of object"""
        return self.name

    class Meta:
        """Metadata for class PlottedShape"""
        verbose_name = 'Plotted Shape'
        verbose_name_plural = 'Plotted Shapes'

CHOICES_ALL = (('0', 'None'), ('1', 'All'), ('2', 'Allow Selection'))

class RoleMaster(models.Model):
    """Role Master Database"""
    name = models.CharField(max_length=2048)
    city = models.IntegerField(choices=CHOICES_ALL)
    slum = models.IntegerField(choices=CHOICES_ALL)
    kml = models.BooleanField(blank=False)
    dynamic_query = models.BooleanField(blank=False)
    predefined_query = models.BooleanField(blank=False)
    can_request = models.BooleanField(blank=False)
    users = models.BooleanField(blank=False)
    create_save_query = models.BooleanField(blank=False)
    deploy_survey = models.BooleanField(blank=False)
    upload_images = models.BooleanField(blank=False)
    prepare_reports = models.BooleanField(blank=False)

    class Meta:
        """Metadata for class RoleMaster"""
        verbose_name = 'Role Master'
        verbose_name_plural = 'Role Masters'

class UserRoleMaster(models.Model):
    """User Role Master Database"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    role_master = models.ForeignKey(RoleMaster, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.DO_NOTHING)
    slum = models.ForeignKey(Slum, on_delete=models.CASCADE)

    class Meta:
        """Metadata for class UserRoleMaster"""
        verbose_name = 'User Role Master'
        verbose_name_plural = 'User Role Masters'


class ProjectMaster(models.Model):
    """Project Master Database"""
    created_user = models.CharField(max_length=2048)
    created_date = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        """Metadata for class ProjectMaster"""
        verbose_name = 'Project Master'
        verbose_name_plural = 'Project Masters'

def validate_image(fieldfile_obj):
    filesize = fieldfile_obj.file.size
    megabyte_limit = 3.0
    if filesize > megabyte_limit*1024*1024:
        raise ValidationError("Max file size is %sMB" % str(megabyte_limit))

class Rapid_Slum_Appraisal(models.Model):
    def validate_image(fieldfile_obj):
        filesize = fieldfile_obj.file.size
        megabyte_limit = 3.0
        if filesize > megabyte_limit*1024*1024:
            raise ValidationError("Max file size is %sMB" % str(megabyte_limit))
    slum_name = models.ForeignKey(Slum, on_delete=models.CASCADE)
    approximate_population=models.CharField(max_length=2048,blank=True, null=True)
    toilet_cost=models.CharField(max_length=2048,blank=True, null=True)
    toilet_seat_to_persons_ratio = models.CharField(max_length=2048,blank=True, null=True)
    percentage_with_an_individual_water_connection = models.CharField(max_length=2048,blank=True, null=True)
    frequency_of_clearance_of_waste_containers = models.CharField(max_length=2048,blank=True, null=True)
    general_info_left_image = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    toilet_info_left_image = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    waste_management_info_left_image = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    water_info_left_image = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    roads_and_access_info_left_image = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    drainage_info_left_image = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    gutter_info_left_image = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    general_image_bottomdown1 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    general_image_bottomdown2 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    toilet_image_bottomdown1 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    toilet_image_bottomdown2 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    waste_management_image_bottomdown1 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    waste_management_image_bottomdown2 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    water_image_bottomdown1  = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    water_image_bottomdown2 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    roads_image_bottomdown1 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    road_image_bottomdown2  = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    drainage_image_bottomdown1 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    drainage_image_bottomdown2 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    gutter_image_bottomdown1  = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    gutter_image_bottomdown2 = models.ImageField(validate_image,upload_to=SHELTER_PHOTO,blank=True, null=True)
    drainage_report_image = models.ImageField(upload_to=DRAINAGE_PHOTO,blank=True, null=True)
    location_of_defecation = models.CharField(max_length=2048,blank=True, null=True)
    percentage_with_individual_toilet = models.CharField(max_length=2048,blank=True, null=True)
    drainage_coverage = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return (self.slum_name.name)

    class Meta:
        permissions = (
            ("can_generate_reports", "Can generate reports"),
        )
        ordering = ['slum_name']



class drainage(models.Model):
    def validate_image(fieldfile_obj):
        filesize = fieldfile_obj.file.size
        megabyte_limit = 3.0
        if filesize > megabyte_limit*1024*1024:
            raise ValidationError("Max file size is %sMB" % str(megabyte_limit))
    slum_name = models.ForeignKey(Slum, on_delete=models.CASCADE)
    drainage_image = models.ImageField(upload_to=DRAINAGE_PHOTO,blank=True, null=True)
