from django.contrib import messages
from django.shortcuts import redirect, render

from . import services


def _get_student_summary(student_pk):
    """Look up student via Student Management service when available."""
    try:
        from students import services as student_services
        return student_services.get_student(student_pk)
    except ImportError:
        return {
            'id': student_pk,
            'student_id': f'#{student_pk}',
            'full_name': f'Student #{student_pk}',
        }


def fee_list(request):
    rows = []
    for ledger in services.list_ledgers():
        student = _get_student_summary(ledger['student_ref']) or {
            'id': ledger['student_ref'],
            'student_id': f"#{ledger['student_ref']}",
            'full_name': f"Student #{ledger['student_ref']}",
        }
        rows.append({'student': student, 'ledger': ledger})
    return render(request, 'finance/list.html', {'rows': rows})


def fee_detail(request, student_pk):
    student = _get_student_summary(student_pk)
    ledger = services.get_ledger(student_pk)
    if student is None or ledger is None:
        return render(request, '404.html', status=404)
    error = ''
    if request.method == 'POST':
        try:
            services.update_total_fee(
                student_pk,
                request.POST.get('total_fee'),
                request.POST.get('reason'),
                changed_by=request.user.get_username(),
            )
            messages.success(request, 'Total fee updated.')
            return redirect('finance:detail', student_pk=student_pk)
        except services.FeeError as exc:
            error = str(exc)
    return render(request, 'finance/detail.html', {
        'student': student,
        'ledger': ledger,
        'history': services.get_history(student_pk),
        'error': error,
        'values': request.POST if request.method == 'POST' else {},
    })
