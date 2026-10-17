from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Yorum, Favori, Puanlama, KullaniciRotasi, RotaDuragi, IletisimMesaji, GeziPaylasimi, GeziPaylasimBegeni,GeziPaylasimYorum
from .models import Profil

admin.site.register(Yorum)
admin.site.register(Favori)
admin.site.register(Puanlama)
admin.site.register(KullaniciRotasi)
admin.site.register(RotaDuragi)
admin.site.register(IletisimMesaji)
admin.site.register(GeziPaylasimi)
admin.site.register(GeziPaylasimBegeni)
admin.site.register(GeziPaylasimYorum)
admin.site.register(Profil)