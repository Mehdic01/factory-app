from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def task_list(request):
    return render(request, "tasks/task_list.html", {"active": "tasks"})
