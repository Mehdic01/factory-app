from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def feedback_list(request):
    return render(request, "feedbacks/feedback_list.html", {"active": "feedbacks"})
