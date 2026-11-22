from django.contrib import messages
from django.shortcuts import redirect, render

from accounts.guards import student_required, warden_required

from . import services


def _get_student_summary(student_pk):
    """Look up student via Student Management service when available."""
    try:
        from hostel import student_service
        student = student_service.get_student(student_pk)
        if student is not None:
            return {
                'id': student.pk,
                'student_id': student.student_id,
                'full_name': student.full_name,
            }
    except ImportError:
        pass
    return {
        'id': student_pk,
        'student_id': f'#{student_pk}',
        'full_name': f'Student #{student_pk}',
    }


@warden_required
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


@warden_required
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


def _resolve_logged_in_student(user):
    """Resolve the Student record for the logged-in student user via Student service."""
    from hostel.models import Student
    from hostel import student_service

    student = Student.objects.filter(user_id=user.pk).first()
    if student is None:
        student = student_service.get_student_by_id(user.username)
    return student


@student_required
def student_fee_and_proofs(request):
    """Student own-fee summary, payment-proof submission, and proof history (VS-09, FR-04)."""
    student = _resolve_logged_in_student(request.user)
    if student is None:
        return render(request, 'finance/student_fees.html', {
            'student': None,
            'ledger': None,
            'payments': [],
            'error': 'No student record is linked to your account yet.',
            'values': {},
        })

    error = ''
    if request.method == 'POST':
        try:
            services.submit_payment_proof(
                student_ref=student.pk,
                owner_user_id=request.user.pk,
                amount=request.POST.get('amount'),
                payment_date=request.POST.get('payment_date'),
                proof_file=request.FILES.get('proof_file'),
            )
            messages.success(request, 'Payment proof submitted and marked Pending for warden verification.')
            return redirect('finance_student:my_fees')
        except services.FeeError as exc:
            error = str(exc)

    return render(request, 'finance/student_fees.html', {
        'student': student,
        'ledger': services.get_ledger(student.pk),
        'payments': services.list_student_payments(student.pk),
        'error': error,
        'values': request.POST if request.method == 'POST' else {},
    })
