from django.shortcuts import render

def report_dashboard(request):
    return render(request, 'reports/dashboard.html')
