from django.db import models
from django.contrib.auth.models import User
import uuid


class Yorum(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    sehir_slug = models.CharField(max_length=100)
    ilce_slug = models.CharField(max_length=100)
    baslik = models.CharField(max_length=150, blank=True)
    yorum = models.TextField()
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kullanici.username} - {self.ilce_slug}"


class Favori(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    sehir_slug = models.CharField(max_length=100)
    ilce_slug = models.CharField(max_length=100)
    yer_baslik = models.CharField(max_length=200)
    yer_turu = models.CharField(max_length=100, blank=True)
    eklenme_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("kullanici", "sehir_slug", "ilce_slug", "yer_baslik")

    def __str__(self):
        return f"{self.kullanici.username} - {self.yer_baslik}"


class Puanlama(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    sehir_slug = models.CharField(max_length=100)
    ilce_slug = models.CharField(max_length=100)
    puan = models.PositiveSmallIntegerField()
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("kullanici", "sehir_slug", "ilce_slug")

    def __str__(self):
        return f"{self.kullanici.username} - {self.ilce_slug} - {self.puan}"


class KullaniciRotasi(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    baslik = models.CharField(max_length=150)
    aciklama = models.TextField(blank=True)
    sehir_slug = models.CharField(max_length=100)
    paylasim_kodu = models.UUIDField(default=uuid.uuid4, editable=False)
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.baslik


class RotaDuragi(models.Model):
    rota = models.ForeignKey(KullaniciRotasi, on_delete=models.CASCADE, related_name="duraklar")
    yer_adi = models.CharField(max_length=200)
    notlar = models.TextField(blank=True)
    sira = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["sira"]

    def __str__(self):
        return self.yer_adi


class IletisimMesaji(models.Model):
    ad = models.CharField(max_length=100)
    email = models.EmailField()
    konu = models.CharField(max_length=150)
    mesaj = models.TextField()
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ad} - {self.konu}"


class GeziPaylasimi(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    baslik = models.CharField(max_length=150)
    sehir_slug = models.CharField(max_length=100)
    aciklama = models.TextField()
    fotograf = models.ImageField(upload_to="gezi_paylasimlari/")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.baslik


class GeziPaylasimBegeni(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    paylasim = models.ForeignKey(GeziPaylasimi, on_delete=models.CASCADE, related_name="begeniler")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("kullanici", "paylasim")

    def __str__(self):
        return f"{self.kullanici.username} - {self.paylasim.baslik}"



class GeziPaylasimYorum(models.Model):
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE)
    paylasim = models.ForeignKey(GeziPaylasimi, on_delete=models.CASCADE, related_name="yorumlar")
    yorum = models.TextField()
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.kullanici.username} - {self.paylasim.baslik}"



class Profil(models.Model):
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profil")
    fotograf = models.ImageField(upload_to="profil_fotograflari/", blank=True, null=True)

    def __str__(self):
        return self.kullanici.username
