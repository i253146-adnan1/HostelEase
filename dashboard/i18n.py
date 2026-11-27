"""Presentation-only English/Urdu localization helper for the Warden Dashboard (VS-23).

Stores the UI language preference in the existing server-side Django session
(ADR-003) with zero database schema changes and clean English fallback.
"""

WARDEN_DASHBOARD_LANG_SESSION_KEY = 'warden_dashboard_lang'
SUPPORTED_LANGS = ('en', 'ur')

_WARDEN_STRINGS = {
    'en': {
        'page_title': 'Warden Dashboard — HostelEase',
        'welcome_eyebrow': 'Welcome to HostelEase',
        'welcome_prefix': 'Welcome,',
        'portal_subtitle': 'Warden Portal — Manage hostel operations and student records with ease.',
        'display_picture': 'Display Picture',
        'change_password': 'Change Password',
        'pending_overview': 'Pending Items Overview',
        'total_pending': 'Total Pending:',
        'pending_payment_proofs': 'Pending Payment Proofs',
        'status_pending': 'Status: Pending',
        'review_proofs': 'Review Proofs',
        'open_complaints': 'Open Complaints',
        'status_complaints': 'Status: Submitted / In Progress',
        'manage_complaints': 'Manage Complaints',
        'pending_room_requests': 'Pending Room Requests',
        'review_requests': 'Review Requests',
        'pending_leave_requests': 'Pending Leave Requests',
        'active_leave_requests': 'Active via Leave Requests',
        'leave_module_pending': 'Leave module pending (VS-15)',
        'hostel_info_title': 'Hostel Information',
        'hostel_info_desc': 'Publish announcements, mess menu, and hostel rules.',
        'announcements': 'Announcements',
        'mess_menu': 'Mess Menu',
        'hostel_rules': 'Hostel Rules',
        'students_rooms_title': 'Students & Rooms',
        'students_rooms_desc': 'Manage student accounts, room capacity, and allocations.',
        'student_management': 'Student Management',
        'room_management': 'Room Management',
        'room_swap_requests': 'Room & Swap Requests',
        'finance_ops_title': 'Finance & Operations',
        'finance_ops_desc': 'Review payment proofs, complaints, leave, visitors, and meals.',
        'fees_payments': 'Fees & Payments',
        'complaints': 'Complaints',
        'leave_requests': 'Leave Requests',
        'visitor_log': 'Visitor Log',
        'meal_optouts': 'Meal Opt-Outs',
        'feedback_summary': 'Feedback Summary',
        # Navigation (used on Warden Dashboard when Urdu is active)
        'nav_overview': 'Overview',
        'nav_dashboard': 'Dashboard',
        'nav_residents_rooms': 'Residents & Rooms',
        'nav_students': 'Students',
        'nav_rooms': 'Rooms',
        'nav_room_requests': 'Room Requests',
        'nav_finance': 'Finance',
        'nav_fee_ledger': 'Fee Ledger',
        'nav_pending_proofs': 'Pending Proofs',
        'nav_operations': 'Operations',
        'nav_feedback': 'Feedback',
        'nav_hostel_info': 'Hostel Info',
        'nav_rules': 'Rules',
        'nav_logout': 'Logout',
    },
    'ur': {
        'page_title': 'وارڈن ڈیش بورڈ — ہاسٹل ایز',
        'welcome_eyebrow': 'ہاسٹل ایز میں خوش آمدید',
        'welcome_prefix': 'خوش آمدید،',
        'portal_subtitle': 'وارڈن پورٹل — ہاسٹل کے امور اور طلبہ کے ریکارڈ آسانی سے منظم کریں۔',
        'display_picture': 'پروفائل تصویر',
        'change_password': 'پاس ورڈ تبدیل کریں',
        'pending_overview': 'زیرِ التواء امور کا جائزہ',
        'total_pending': 'کل زیرِ التواء:',
        'pending_payment_proofs': 'زیرِ التواء ادائیگی کے ثبوت',
        'status_pending': 'حیثیت: زیرِ التواء',
        'review_proofs': 'ثبوتوں کا جائزہ لیں',
        'open_complaints': 'زیرِ غور شکایات',
        'status_complaints': 'حیثیت: جمع شدہ / جاری',
        'manage_complaints': 'شکایات منظم کریں',
        'pending_room_requests': 'زیرِ التواء کمرے کی درخواستیں',
        'review_requests': 'درخواستوں کا جائزہ لیں',
        'pending_leave_requests': 'زیرِ التواء رخصت کی درخواستیں',
        'active_leave_requests': 'رخصت کی درخواستیں دیکھیں',
        'leave_module_pending': 'رخصت کا ماڈیول زیرِ التواء ہے (VS-15)',
        'hostel_info_title': 'ہاسٹل کی معلومات',
        'hostel_info_desc': 'اعلانات، میس مینو اور ہاسٹل کے قواعد شائع کریں۔',
        'announcements': 'اعلانات',
        'mess_menu': 'میس مینو',
        'hostel_rules': 'ہاسٹل کے قواعد',
        'students_rooms_title': 'طلبہ اور کمرے',
        'students_rooms_desc': 'طلبہ کے اکاؤنٹس، کمروں کی گنجائش اور الاٹمنٹ منظم کریں۔',
        'student_management': 'طلبہ کا انتظام',
        'room_management': 'کمروں کا انتظام',
        'room_swap_requests': 'کمرے اور تبدیلی کی درخواستیں',
        'finance_ops_title': 'مالیات اور آپریشنز',
        'finance_ops_desc': 'ادائیگی کے ثبوت، شکایات، رخصت، ملاقاتی اور کھانے کا جائزہ لیں۔',
        'fees_payments': 'فیس اور ادائیگیاں',
        'complaints': 'شکایات',
        'leave_requests': 'رخصت کی درخواستیں',
        'visitor_log': 'ملاقاتیوں کا ریکارڈ',
        'meal_optouts': 'کھانے سے دستبرداری',
        'feedback_summary': 'تاثرات کا خلاصہ',
        # Navigation
        'nav_overview': 'جائزہ',
        'nav_dashboard': 'ڈیش بورڈ',
        'nav_residents_rooms': 'رہائشی اور کمرے',
        'nav_students': 'طلبہ',
        'nav_rooms': 'کمرے',
        'nav_room_requests': 'کمرے کی درخواستیں',
        'nav_finance': 'مالیات',
        'nav_fee_ledger': 'فیس کھاتہ',
        'nav_pending_proofs': 'زیرِ التواء ثبوت',
        'nav_operations': 'آپریشنز',
        'nav_feedback': 'تاثرات',
        'nav_hostel_info': 'ہاسٹل معلومات',
        'nav_rules': 'قواعد',
        'nav_logout': 'لاگ آؤٹ',
    },
}


def get_warden_dashboard_lang(request):
    """Return the normalized Warden Dashboard UI language ('en' or 'ur')."""
    lang = request.session.get(WARDEN_DASHBOARD_LANG_SESSION_KEY, 'en')
    return lang if lang in SUPPORTED_LANGS else 'en'


def set_warden_dashboard_lang(request, lang):
    """Persist a validated Warden Dashboard UI language in the session."""
    normalized = lang if lang in SUPPORTED_LANGS else 'en'
    request.session[WARDEN_DASHBOARD_LANG_SESSION_KEY] = normalized
    return normalized


def get_warden_dashboard_i18n(request):
    """Build presentation context for Warden Dashboard English/Urdu rendering."""
    lang = get_warden_dashboard_lang(request)
    is_urdu = lang == 'ur'
    return {
        'lang': lang,
        'is_urdu': is_urdu,
        'dir': 'rtl' if is_urdu else 'ltr',
        't': _WARDEN_STRINGS[lang],
    }
