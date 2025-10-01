from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Create your views here.
@login_required
def announcement_list(request):
    return render(request, "comms/announcement_list.html", {"active": "comms"})
