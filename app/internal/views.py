import json
import csv
import io
import operator
import random

from django.views.decorators.http import require_POST
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied

from app.event.utils import generate_team_id
from app.event.models import Event, Registration
from app.main.models import MUser, Profile
from app.workshop.models import Workshop
from app.payment.models import Invoice

from .forms import RegistrationForm
from app.main.utils import template_email


def recipt_view(req, rid=None):
    user = None

    # allow admins to access receipts using ids
    if rid is not None and req.user.is_authenticated() and req.user.is_staff:
        try:
            uid = int(rid)

            # guard the improbable case where hash is all numeric
            if uid < 999999:
                user = get_object_or_404(MUser, id=MUser.get_real_id(uid))
        except:
            pass

    if user is None:
        if rid is not None:
            user = get_object_or_404(Profile, receipt_id=rid).user
        else:
            if not req.user.is_authenticated():
                raise Http404

            user = req.user

    registrations = Registration.objects.filter(profile=user.profile)
    workshops = user.profile.registered_workshops.all()

    if settings.DEBUG:
        template = 'magnovite/recipt.html'
    else:
        template = 'magnovite/dist/recipt.html'

    return render(req, template, {
        'user': user,
        'profile': user.profile,
        'registrations': registrations,
        'workshops': workshops
    })


def accounts_view(req):
    if not req.user.is_staff:
        raise PermissionDenied

    invoices = Invoice.objects.filter(success=True).prefetch_related('profile').order_by('-id')

    transactions = [
        {
            'title': 'Single Pack',
            'invoices': invoices.filter(invoice_type='single')
        },
        {
            'title': 'Multiple Pack',
            'invoices': invoices.filter(invoice_type='multiple')
        },
        {
            'title': 'Group Events',
            'invoices': invoices.filter(invoice_type='team')
        },
        {
            'title': 'Upgrade from Single to Multiple',
            'invoices': invoices.filter(invoice_type='upgrade')
        },
        {
            'title': 'Workshop',
            'invoices': invoices.filter(invoice_type='workshop')
        },
        {
            'title': 'Hospitality',
            'invoices': invoices.filter(invoice_type='hospitality')
        }
    ]

    if settings.DEBUG:
        template = 'magnovite/internalAccounts.html'
    else:
        template = 'magnovite/dist/internalAccounts.html'

    return render(req, template, {
        'transactions': transactions,
        'total': invoices.count(),
        'now': timezone.now()
    })


def all_table_view(req):
    if not req.user.is_staff:
        raise PermissionDenied

    profiles = Profile.prefetch_all(Profile.objects.all())

    if settings.DEBUG:
        template = 'magnovite/fullTable.html'
    else:
        template = 'magnovite/dist/fullTable.html'

    return render(req, template, {
        'now': timezone.now(),
        'profiles': profiles
    })


def private_view(req, type, slug):
    """
    Private view for private urls of events and workshops
    shows a table of registrations
    """
    if not type in ('workshop', 'event'):
        raise Http404

    workshop, event = None, None
    if type == 'workshop':
        workshop = get_object_or_404(Workshop, private_slug=slug)
    else:
        event = get_object_or_404(Event, private_slug=slug)

    return show_table_view(req, type, event, workshop)


def table_view(req, type, slug=None):
    if not req.user.is_staff:
        raise PermissionDenied

    if not type in ('workshop', 'event', 'hospitality', 'on-spot', 'checked-in', 'colleges'):
        raise Http404

    workshop, event = None, None
    if type == 'workshop':
        workshop = get_object_or_404(Workshop, slug=slug)
    elif type == 'event':
        event = get_object_or_404(Event, slug=slug)

    return show_table_view(req, type, event, workshop)


def show_table_view(req, type, event=None, workshop=None):
    """
    Shows a given workshop or event
    This is not used in the URL conf, but called by other views
    """
    days = ''

    if settings.DEBUG:
        template = 'magnovite/table_view.html'
    else:
        template = 'magnovite/dist/table_view.html'

    if type == 'workshop':
        profiles = workshop.profile_set.all().prefetch_related('user').order_by('name')
    elif type == 'event':
        profiles = event.profile_set.all().prefetch_related('user')
    elif type == 'hospitality':
        profiles = Profile.objects.filter(hospitality_days__gt=0)
    elif type == 'on-spot':
        profiles = Profile.objects.filter(on_spot=True).order_by('id')

        days = 'Both'
        if 'day' in req.GET:
            if req.GET.get('day', '') == '1':
                days = 'First'
                profiles = profiles.filter(checked_in_first_day=True)
            else:
                days = 'Second'
                profiles = profiles.filter(checked_in_first_day=False)

        profiles = Profile.prefetch_all(profiles)
    elif type == 'checked-in':
        profiles = Profile.objects.filter(checked_in=True).order_by('id')

        days = 'Both'
        if 'day' in req.GET:
            if req.GET.get('day', '') == '1':
                days = 'First'
                profiles = profiles.filter(checked_in_first_day=True)
            else:
                days = 'Second'
                profiles = profiles.filter(checked_in_first_day=False)

        profiles = Profile.prefetch_all(profiles)
    elif type == 'colleges':
        profiles = Profile.objects.filter(checked_in=True).values('college').annotate(total=Count('college'))

        if req.GET.get('order', '') == 'college':
            profiles = profiles.order_by('college')
        else:
            profiles = profiles.order_by('-total')

    return render(req, template, {
        'type': type,
        'workshop': workshop,
        'event': event,
        'profiles': profiles,
        'now': timezone.now(),
        'days': days
    })


def register_view(req):
    if not (req.user.is_staff and req.user.has_perm('main.on_spot_registration')):
        raise PermissionDenied

    if settings.DEBUG:
        template = 'magnovite/internalRegistration.html'
    else:
        template = 'magnovite/dist/internalRegistration.html'

    events = Event.objects.all()
    workshops = Workshop.objects.all()

    obj = {
        'technical': [],
        'cultural': [],
        'group': [],
        'workshop': []
    }

    for event in events:
        _o = {
            'id': event.id,
            'title': event.title,
            'closed': event.reg_closed
        }

        if event.is_multiple():
            _o['is_team'] = True
            _o['team_min'] = event.team_min
            _o['team_max'] = event.team_max

        if event.team_type == 'group':
            obj['group'].append(_o)
        elif event.technical:
            obj['technical'].append(_o)
        else:
            obj['cultural'].append(_o)

    for workshop in workshops:
        obj['workshop'].append({
            'id': workshop.id,
            'title': workshop.title,
            'price': workshop.price
        })

    return render(req, template, {
        'jsonobj': json.dumps(obj)
    })


def register_multiple_view(req):
    if settings.DEBUG:
        template = 'magnovite/internalMultipleRegistration.html'
    else:
        template = 'magnovite/dist/internalMultipleRegistration.html'

    cult = Event.objects.filter(technical=False, team_type='team')
    tech = Event.objects.filter(technical=True, team_type='team')
    group = Event.objects.filter(team_type='group')

    return render(req, template, {
        'cult': cult,
        'tech': tech,
        'group': group
    })


@require_POST
def register_multiple(req):
    if not (req.user.is_staff and req.user.has_perm('main.on_spot_registration')):
        raise PermissionDenied

    try:
        data = json.loads(req.body.decode('utf-8'))
    except ValueError:
        return JsonResponse({
            'status': 'error',
            'errorMessage': 'Invalid JSON'
        }, status=400)

    success_obj = []

    events = []
    for event in data['events']:
        event = Event.objects.get(id=event)
        team_id = generate_team_id(str(random.random()) + str(random.random()), event)

        events.append((event, team_id))

    for i, member in enumerate(data['members']):
        email = member.get('email', '')
        if not email:
            email = str(i) + '|' + member['name'][:10] + '|' + member['college'][:5] + '@onspotteam.com'
            email = email.replace(' ', '_')

        user = MUser.objects.create_user(email=email)

        profile = user.profile
        profile.name = member['name']
        profile.college = member['college']
        profile.mobile = member.get('mobile', '')
        profile.pack = data['pack']
        profile.auth_provider = 'on-spot-team'

        profile.on_spot = True
        profile.checked_in = True
        profile.on_spot_registerer = req.user.profile.name

        profile.save()

        success_obj.append({
            'name': profile.name,
            'id': user.get_id()
        })

        for event, team_id in events:
            Registration.objects.create(
                event=event,
                profile=profile,
                team_id=team_id,
                on_spot=True,
                mode='on-spot-team',
            )

    return JsonResponse({
        'status': 'success',
        'data': success_obj
    })

@require_POST
def register_create(req):
    if not (req.user.is_staff and req.user.has_perm('main.on_spot_registration')):
        raise PermissionDenied

    # IN params
    # name, email, college, mobile, referred, pack, events[{id, teamid?}], workshops[id]
    try:
        data = json.loads(req.body.decode('utf-8'))
    except ValueError:
        return JsonResponse({
            'status': 'error',
            'errorMessage': 'Invalid JSON'
        }, status=400)

    f = RegistrationForm(data)
    if not f.is_valid():
        return JsonResponse({
            'status': 'error',
            'errors': f.errors
        }, status=400)

    workshops_objs = data.get('workshops', [])
    events_objs = data.get('events', [])

    events = []
    workshops = []

    # validate events passed in
    for event_obj in events_objs:
        if event_obj.get('id', '') == '':
            return JsonResponse({
                'status': 'error',
                'errors': {'form': ['Event ID not given']}
            }, status=400)

        try:
            event = Event.objects.get(id=event_obj['id'])
            events.append(event)
        except Event.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'errors': {'form': ['Invalid Event ID']}
            }, status=400)

        # validate teamids
        team_id = event_obj.get('teamid', '')
        if team_id != '':
            regs = Registration.objects.filter(team_id=team_id, event=event).count()
            if regs == 0:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'tid-' + str(event.id): ['Invalid team id: ' + team_id]}
                }, status=400)

            elif regs == event.team_max:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'tid-' + str(event.id): ['Team (' + team_id + ') is full']}
                }, status=400)

    # validate workshops passed in
    for workshop_obj in workshops_objs:
        if not workshop_obj.get('id', ''):
            return JsonResponse({
                'status': 'error',
                'errrors': {'form': ['Invalid Workshop ID']}
            }, status=400)

        try:
            workshop = Workshop.objects.get(id=workshop_obj['id'])
            workshops.append(workshop)
        except Workshop.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'errors': {'form': ['Invalid Workshop ID']}
            }, status=400)

    # validate pack/event combination
    num_quota_events = 0
    for event in events:
        if event.team_type in ('individual', 'team'):
            num_quota_events += 1

    if f.cleaned_data['pack'] == 'single' and num_quota_events > 1:
        return JsonResponse({
            'status': 'error',
            'errors': {'pack': ['Cant register to more than one individual/team event on single pack']}
        }, status=400)

    elif f.cleaned_data['pack'] == 'none' and num_quota_events > 0:
        return JsonResponse({
            'status': 'error',
            'errors': {'pack': ['Cant register to individual/team events on No Pack']}
        }, status=400)

    try:
        MUser.objects.get(email=f.cleaned_data['email'])

        # duplicate user
        return JsonResponse({
            'status': 'error',
            'errors': {'email': ['This user is already registered']}
        }, status=400)
    except MUser.DoesNotExist:
        user = MUser.objects.create_user(email=f.cleaned_data['email'])

    # calculate payment due
    if f.cleaned_data['pack'] == 'single':
        payment = 100
    elif f.cleaned_data['pack'] == 'multiple':
        payment = 200
    else:
        payment = 0

    # setup profile
    profile = user.profile
    profile.name=f.cleaned_data['name']
    profile.college=f.cleaned_data['college']
    profile.mobile=f.cleaned_data['mobile']
    profile.referral=f.cleaned_data.get('referred', '')
    profile.pack=f.cleaned_data['pack']
    profile.auth_provider='on-spot'

    profile.on_spot = True
    profile.checked_in = True
    profile.on_spot_registerer = req.user.profile.name
    # profile saved at the end

    success_obj = {
        'name': profile.name,
        'multipleEvents': []
    }

    # do event registrations
    for i, event in enumerate(events):
        team_id = events_objs[i].get('teamid', '')
        is_owner = False

        if event.is_multiple():
            # if team_id given it would already be validated above
            if team_id == '':
                team_id = generate_team_id(user.email, event)

                if event.is_group():
                    is_owner = True

                    # creating group team, cost 500
                    payment += 500

            success_obj['multipleEvents'].append({
                'id': event.id,
                'title': event.title,
                'teamid': team_id
            })

        Registration.objects.create(
            event=event,
            profile=profile,
            team_id=team_id,
            is_owner=is_owner,
            on_spot=True,
            mode='on-spot'
        )

    # do workshop registrations
    for workshopObj in workshops:
        payment += workshop.price
        profile.registered_workshops.add(workshop)

    profile.total_payment = payment
    profile.save()

    # template_email(
    #     'server@magnovite.net',
    #     (user.email,),
    #     'Welcome to Magnovite 2015',
    #     'on_spot_receipt',
    #     {'profile': profile}
    # )

    success_obj['data'] = {
        'id': user.get_id(),
        'name': profile.name
    }

    success_obj['status'] = 'success'
    success_obj['reciptURL'] = '/receipt/' + profile.receipt_id + '/'

    return JsonResponse(success_obj)


def api_checkin(req, uid):
    if not req.user.is_staff:
        raise PermissionDenied

    user = get_object_or_404(MUser, id=MUser.get_real_id(uid))
    user.profile.checked_in = True
    user.profile.save()

    return HttpResponse()


def api_checkout(req, uid):
    if not req.user.is_staff:
        raise PermissionDenied

    user = get_object_or_404(MUser, id=MUser.get_real_id(uid))
    user.profile.checked_in = False
    user.profile.save()

    return HttpResponse()


def api_items(req):
    out = {
        'events': {
            'technical': [],
            'cultural': [],
            'group': []
        },
        'workshops': []
    }

    for event in Event.objects.all():
        _o = {
            'id': event.id,
            'title': event.title,
            'slug': event.slug
        }

        if event.is_multiple():
            _o['is_team'] = True
            _o['team_min'] = event.team_min
            _o['team_max'] = event.team_max

        if event.team_type == 'group':
            out['events']['group'].append(_o)
        elif event.technical:
            out['events']['technical'].append(_o)
        else:
            out['events']['cultural'].append(_o)

    for workshop in Workshop.objects.all():
        out['workshops'].append({
            'id': workshop.id,
            'title': workshop.title,
        })

    return JsonResponse(out)


@csrf_exempt
def test(req):
    # Closed
    raise PermissionDenied

    if req.GET.get('secret') != settings.SECRET_KEY[:5]:
        return JsonResponse({'status': 'unauthorized'}, status=403)

    try:
        data = json.loads(req.body.decode('utf-8'))['data']
    except ValueError:
        return JsonResponse({
            'status': 'error',
            'errorMessage': 'Invalid JSON'
        }, status=400)

    print(len(data))
    for obj in data:
        user = MUser.objects.create_user(email=obj['email'])

        profile = user.profile
        profile.name = obj['name']
        profile.college = obj['college']
        profile.mobile = obj['mobile']
        profile.pack = obj['pack']
        profile.auth_provider = 'publicity'
        profile.remarks = obj['remarks']

        for id in obj['events']:
            try:
                event = Event.objects.get(id=id)
            except Event.DoesNotExist:
                return JsonResponse({'error': 'Invalid event ' + str(id)})

            team_id = ''
            is_owner = False
            if event.is_multiple():
                team_id = generate_team_id(user.email, event)

                if event.is_group():
                    is_owner = True

            Registration.objects.create(
                event=event,
                profile=profile,
                team_id=team_id,
                is_owner=is_owner,
                mode='publicity'
            )

        profile.save()

    return JsonResponse({'status': 'success'})


def all_csv(req):
    if not req.user.is_superuser:
        raise PermissionDenied

    try:
        min_id = int(req.GET.get('from_id', '0'))
    except ValueError:
        return HttpResponse(status=400)

    EVENT_MAP = {
        'DEFC':1, 'DANC':4, 'GCS':5, 'CTYC':6, 'WEBD':7, 'TEKH':8,
        'PRJ':9, 'CADM':11, 'JYW':12, 'CANG':13, 'LDSC':14, 'BLDR':15,
        'PPR':16, 'RBW':18, 'WATR':19, 'LINE':20, 'CDBG':21, 'THT':22,
        'CMCS':23, 'ARTR':24, 'PHOT':25, 'DMBC':26, 'QUIZ':27,
        'POTP':28, 'JAM':29, 'DBTE':31, 'INDM':32, 'WSEL':33, 'ACOU':34,
        'KRKE':35, 'BBOY':36, 'SWTCH':37, 'OVNC':38, 'ANDV':39,
        'GNFS':40, 'CADC':41, 'INSW':42, 'SOLO':44,
    }

    INV_EVENT_MAP = {v: k for k, v in EVENT_MAP.items()}

    base = Profile.objects.filter(id__gt=MUser.get_real_id(min_id))

    not_none = base.filter(~Q(pack='none')).prefetch_related('user')

    only_group = base.filter(pack='none')
    only_group = only_group.annotate(Count('registered_events'))
    only_group = only_group.filter(registered_events__count__gt=0).prefetch_related('user')

    not_none = not_none.prefetch_related('registered_events')
    only_group = only_group.prefetch_related('registered_events')

    out = []
    for obj in list(not_none) + list(only_group):
        if obj.pack == 'single':
            type = 'Single'
        elif obj.pack == 'multiple':
            type = 'Multiple'
        else:
            type = 'Group'

        event = '-'
        if type == 'Single':
            _event = obj.registered_events.first()
            if _event:
                event = INV_EVENT_MAP[_event.id]

        elif type == 'Group':
            for _event in obj.registered_events.all():
                if event == '-':
                    event = ''

                event = INV_EVENT_MAP[_event.id] + ', '

            event = event.strip(' ,')

        out.append([
            obj.user.get_id(), #id
            obj.name.title(), #name
            obj.college, #college
            type, # type
            event
        ])

    # mark all selected as id printed
    not_none.update(id_printed=True)

    for obj in only_group:
        obj.id_printed = True
        obj.save()

    out = sorted(out, key=lambda x: int(x[0]))

    filename = 'mag_' + str(out[0][0]) + '_' + str(out[-1][0]) + '.csv'

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

    writer = csv.writer(response)
    for row in out:
        writer.writerow(row)

    return response


def user_list(req):
    if not req.user.is_authenticated() and req.user.is_staff:
        raise PermissionDenied

    profiles = Profile.objects.all()

    if 'name' in req.GET:
        query_param = 'Name'
        query = req.GET.get('name', '')
        profiles = profiles.filter(name__icontains=query)
    elif 'college' in req.GET:
        query_param = 'College'
        query = req.GET.get('college', '')
        profiles = profiles.filter(college__icontains=query)
    elif 'mobile' in req.GET:
        query_param = 'Mobile'
        query = req.GET.get('mobile', '')
        profiles = profiles.filter(college__icontains=query)
    else:
        return JsonResponse({
            'status': 'error',
            'errorMessage': 'Invalid filter param'
        }, status=400)

    if settings.DEBUG:
        template = 'magnovite/internalUserList.html'
    else:
        template = 'magnovite/dist/internalUserList.html'

    return render(req, template, {
        'query': query,
        'query_param': query_param,
        'profiles': profiles,
        'now': timezone.now()
    })
