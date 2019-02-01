from django.shortcuts import render
from .models import Post
from .models import Companies
from django.utils import timezone
from django.shortcuts import render, get_object_or_404


# Create your views here.
def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_lists.html', {'posts': posts})
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

def clist(request):
    companies = Companies.objects.all()
    return render(request, 'blog/nav.html', {'companies': companies})

def clist_detail(request,pk):
    companies = Companies.objects.all()
    comp = get_object_or_404(Companies,pk=pk)
    return render(request, 'blog/nav.html', {'companies': companies,'comp':comp})