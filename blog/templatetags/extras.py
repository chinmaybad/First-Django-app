from django import template
register=template.Library()

@register.filter(name="get_attr")
def get_attr(obj,arg):
	return getattr(obj,arg)

@register.filter(name="hasattribute")
def hasattribute(obj,arg):
	return hasattr(obj,arg)
	
