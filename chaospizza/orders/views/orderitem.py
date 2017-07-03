# pylint: disable=C0111
# pylint: disable=R0201
# pylint: disable=W0201
# pylint: disable=W0613
from django import forms
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib import messages

from ..models import Order, OrderItem
from ..mixins import UserSessionMixin


class CreateOrderItem(UserSessionMixin, CreateView):
    """Add a new order item to an existing order."""

    model = OrderItem
    fields = ['participant', 'description', 'price', 'amount']

    def dispatch(self, request, *args, **kwargs):
        """Ensure that the associated order's state is preparing."""
        self.order = Order.objects.filter(pk=kwargs['order_slug']).get()
        if not self.order.is_preparing:
            messages.add_message(
                request, messages.ERROR,
                'Can not add order item, order is in state {}'.format(self.order.state)
            )
            return redirect('orders:view_order', order_slug=kwargs['order_slug'])
        return super(CreateOrderItem, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Populate the participant name if the user is already known in the session."""
        return {'participant': self.username}

    def get_context_data(self, **kwargs):
        """Load associated Order record."""
        context = super(CreateOrderItem, self).get_context_data(**kwargs)
        context['order'] = self.order
        return context

    def form_valid(self, form):
        """Associate created OrderItem with existing Order and add the participant's name to the session state."""
        try:
            order_item = form.save(commit=False)
            self.order.add_item(
                order_item.participant,
                order_item.description,
                order_item.price,
                order_item.amount
            )
            self.username = order_item.participant
        except ValueError as err:
            messages.add_message(self.request, messages.ERROR, 'Could not add order item: {}'.format(err))
        return redirect('orders:view_order', order_slug=self.kwargs['order_slug'])


class UpdateOrderItemForm(forms.ModelForm):
    """Custom ModelForm for OrderItem where the participant field can not be changed."""

    class Meta:  # noqa
        model = OrderItem
        fields = ['participant', 'description', 'price', 'amount']

    participant = forms.CharField(disabled=True)


class UpdateOrderItem(UserSessionMixin, UpdateView):
    """Update a single order item."""

    model = OrderItem
    slug_field = 'id'
    slug_url_kwarg = 'item_slug'
    form_class = UpdateOrderItemForm

    # TODO make sure user is allowed to edit
    def dispatch(self, request, *args, **kwargs):
        """Ensure that the associated order's state is preparing."""
        self.order = Order.objects.filter(pk=kwargs['order_slug']).get()
        if not self.order.is_preparing:
            messages.add_message(
                request, messages.ERROR,
                'Can not edit order item, order is in state {}'.format(self.order.state)
            )
            return redirect(self.get_success_url())
        return super(UpdateOrderItem, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Load associated Order record."""
        context = super(UpdateOrderItem, self).get_context_data(**kwargs)
        context['order'] = self.order
        return context

    def get_success_url(self):
        """Return order detail view."""
        return reverse('orders:view_order', kwargs={'order_slug': self.kwargs['order_slug']})


class DeleteOrderItem(UserSessionMixin, DeleteView):
    """Delete a single order item."""

    model = OrderItem
    slug_field = 'id'
    slug_url_kwarg = 'item_slug'

    # TODO make sure user is allowed to edit
    def dispatch(self, request, *args, **kwargs):
        """Ensure that the associated order's state is preparing."""
        self.order = Order.objects.filter(pk=kwargs['order_slug']).get()
        if not self.order.is_preparing:
            messages.add_message(
                request, messages.ERROR,
                'Can not delete order item, order is in state {}'.format(self.order.state)
            )
            return redirect(self.get_success_url())
        return super(DeleteOrderItem, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Load associated Order record."""
        context = super(DeleteOrderItem, self).get_context_data(**kwargs)
        context['order'] = self.order
        return context

    def get_success_url(self):
        """Return order detail view."""
        return reverse('orders:view_order', kwargs={'order_slug': self.kwargs['order_slug']})
