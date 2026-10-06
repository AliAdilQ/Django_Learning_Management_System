from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as static_asset
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path(
        "favicon.ico", RedirectView.as_view(url=static_asset("images/favicon.svg"), permanent=True)
    ),
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("assignments/", include("assignments.urls")),
    path("quizzes/", include("quizzes.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler403 = "core.views.error_403"
handler404 = "core.views.error_404"
handler500 = "core.views.error_500"
admin.site.site_header = "Luma Learning · Administration"
admin.site.site_title = "Luma admin"
admin.site.index_title = "Learning platform management"
