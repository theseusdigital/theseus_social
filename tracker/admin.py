# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from tracker.models import User, Keyword, Platform, Handle, Geo, FacebookAccessToken, TwitterAccessToken, GoogleAccessToken, InstagramAccessToken, Brand
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    fields=['username','password','handle','keyword','active']
    list_display=('username','password','linked_handles','linked_keywords','active')
    search_fields=['username']

class HandleAdmin(admin.ModelAdmin):
	search_fields = ['name']
	list_display = ('name','platform','uniqueid','status')
	list_filter = ['platform','status']
	fields = ['name','platform','status','uniqueid','keyword']

class GeoAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbr', 'location')

class KeywordAdmin(admin.ModelAdmin):
	fields = ('name', 'platform', 'active')
	# filter_horizontal = ['platform']
	list_display = ('name', 'linked_platforms', 'active')
	list_filter = ['active', 'platform']
	search_fields = ['name']

class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ('appname', 'usage_stats', 'active')

class GoogleTokenAdmin(admin.ModelAdmin):
    list_display = ('projectname', 'usage_stats', 'active')

class BrandAdmin(admin.ModelAdmin):
    fields=['name','handle','active']
    list_display=('name','linked_handles','active')
    search_fields=['name']

# class UserHandleAdmin(admin.ModelAdmin):
# 	fields=['user','handle']
# 	list_display=('user','handle','get_platform')
# 	list_filter = ['handle__platform']
# 	search_fields=['user__username','handle__handle']

# 	def get_platform(self, obj):
# 		return obj.handle.platform

# 	get_platform.short_description = 'Platform'
# 	get_platform.admin_order_field = 'handle__platform'

admin.site.register(User, UserAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Platform)
admin.site.register(Handle, HandleAdmin)
admin.site.register(Geo, GeoAdmin)
admin.site.register(FacebookAccessToken, AccessTokenAdmin)
admin.site.register(TwitterAccessToken, AccessTokenAdmin)
admin.site.register(GoogleAccessToken, GoogleTokenAdmin)
admin.site.register(InstagramAccessToken, AccessTokenAdmin)
admin.site.register(Brand, BrandAdmin)

