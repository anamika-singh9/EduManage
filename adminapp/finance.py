"""Fee bookkeeping and timetable helpers (kept out of views so they are easy to test)."""
from decimal import Decimal, InvalidOperation
from django.db import transaction
from .models import student, FeePayment, TimetableEntry


def to_decimal(value):
    try:
        return Decimal(str(value or 0))
    except InvalidOperation:
        return Decimal(0)


def fmt(d):
    d = Decimal(d)
    return str(int(d)) if d == d.to_integral() else f"{d:.2f}"


@transaction.atomic
def record_payment(stu, amount, paid_on, mode, reference='', note='', user=None):
    """Create a payment and move the amount from `duefee` to `feepaid`. Raises ValueError on bad input."""
    stu = student.objects.select_for_update().get(pk=stu.pk)
    amount = to_decimal(amount)
    due = to_decimal(stu.duefee)
    if amount <= 0:
        raise ValueError('Amount must be greater than zero.')
    if amount > due:
        raise ValueError(f'Amount exceeds the outstanding due of {fmt(due)}.')
    payment = FeePayment.objects.create(student=stu, amount=amount, paid_on=paid_on, mode=mode,
                                        reference=reference, note=note, recorded_by=user)
    stu.feepaid = fmt(to_decimal(stu.feepaid) + amount)
    stu.duefee = fmt(due - amount)
    stu.save(update_fields=['feepaid', 'duefee'])
    return payment


def fee_summary(queryset=None):
    qs = queryset if queryset is not None else student.objects.all()
    paid = sum((to_decimal(s.feepaid) for s in qs), Decimal(0))
    due = sum((to_decimal(s.duefee) for s in qs), Decimal(0))
    return {'collected': fmt(paid), 'outstanding': fmt(due), 'defaulters': sum(1 for s in qs if to_decimal(s.duefee) > 0)}


def build_grid(entries):
    """Turn timetable rows into [(period, start, end, [entry-or-None for Mon..Sat])] for the template."""
    periods = {}
    for e in entries:
        row = periods.setdefault(e.period, {'start': e.start_time, 'end': e.end_time, 'cells': [None] * 6})
        row['cells'][e.day] = e
    return [(p, r['start'], r['end'], r['cells']) for p, r in sorted(periods.items())]
