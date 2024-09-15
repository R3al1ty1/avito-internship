from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Tender, Bid
from .serializers import TenderSerializer, BidSerializer, ReviewSerializer
from rest_framework import status
from backend.apps.models import Tender, TenderVersion, Bid, BidVersion, Employee, Organization, OrganizationResponsible, Review
from django.db.models import Q
from datetime import datetime
import pytz


@api_view(["GET"])
@permission_classes([AllowAny])
def ping(request):
    """
    Проверка доступности сервера.
    """
    return Response("ok", status=200)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_tenders(request):
    """
    Получить список тендеров с возможностью фильтрации по типу услуг.
    Параметры пагинации: limit (ограничение количества) и offset (смещение).
    """
    service_type = request.GET.get('service_type')

    try:
        limit = int(request.GET.get('limit', 5))
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        return Response({'reason': 'Limit and offset must be integers'}, status=400)

    # Базовый запрос: все тендеры со статусом "PUBLISHED"
    tenders = Tender.objects.filter(status="PUBLISHED")

    # Фильтрация по типу услуг, если параметр указан
    if service_type:
        tenders = tenders.filter(service_type__icontains=service_type)

    tenders = tenders.distinct()[offset:offset+limit]

    serializer = TenderSerializer(tenders, many=True)
    return Response(serializer.data, status=200)




@api_view(["POST"])
@permission_classes([AllowAny])
def create_tender(request):
    """
    Создать новый тендер
    """
    username = request.data.get('creatorUsername')
    organization_id = request.data.get('organizationId')
    
    if not username or not organization_id:
        return Response({"reason": "Missing required fields: 'creatorUsername' and/or 'organizationId'."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Проверка существования пользователя
    try:
        creator = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "Creator with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)
    
    # Проверка существования организации
    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        return Response({"reason": "Organization with the specified ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

    # Проверка, является ли пользователь ответственным за организацию
    is_responsible = OrganizationResponsible.objects.filter(
        organization=organization, 
        user=creator
    ).exists()

    if not is_responsible:
        return Response({"reason": "Creator is not responsible for the organization."}, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    data['creator_username'] = username
    data['organization'] = organization_id
    data['status'] = 'CREATED'

    timezone = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(timezone).strftime("%Y-%m-%dT%H:%M:%SZ")
    data['created_at'] = current_time

    serializer = TenderSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_tenders(request):
    """
    Получение списка тендеров для указанного пользователя по username с поддержкой пагинации (limit и offset).
    """
    username = request.GET.get('username')
    limit = request.GET.get('limit', 5)
    offset = request.GET.get('offset', 0)
    
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        limit = int(limit)
        offset = int(offset)
    except ValueError:
        return Response({"reason": "Limit and offset must be integers."}, status=status.HTTP_400_BAD_REQUEST)

    # Получение всех тендеров пользователя
    tenders = Tender.objects.filter(creator_username=username)

    tenders = tenders[offset:offset + limit]
    
    serializer = TenderSerializer(tenders, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["GET", "PUT"])
@permission_classes([AllowAny])
def tender_status(request, tender_id):
    """
    GET: Возвращает статус тендера.
    PUT: Обновляет статус тендера, если пользователь ответственный за организацию.
    """
    username = request.GET.get('username')

    if not tender_id:
        return Response({"reason": "Tender ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return Response({"reason": "Tender with the specified ID does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

    # Проверка, является ли пользователь ответственным за организацию тендера
    responsible = OrganizationResponsible.objects.filter(
        organization=tender.organization,
        user=user
    ).exists()

    # Обработка GET-запроса
    if request.method == "GET":
        return Response({"status": tender.status}, status=status.HTTP_200_OK)
    
    # Обработка PUT-запроса
    if request.method == "PUT":
        new_status = request.GET.get('status')  # Используем данные из тела запроса для PUT
        if not new_status:
            return Response({"reason": "Status is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка допустимых статусов
        valid_statuses = ['PUBLISHED', 'CLOSED']
        if new_status not in valid_statuses:
            return Response({"reason": f"Invalid status. Valid statuses are: {', '.join(valid_statuses)}."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not responsible and user.username != tender.creator_username:
            return Response({"reason": "User is not authorized to update the status of this tender."}, status=status.HTTP_403_FORBIDDEN)
        
        # Обновляем статус
        tender.status = new_status
        tender.save()

        serializer = TenderSerializer(tender)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([AllowAny])
def edit_tender(request, tender_id):
    """
    Редактирование существующего тендера
    """
    username = request.GET.get('username')
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)
    
    tender = get_object_or_404(Tender, id=tender_id)
    
    responsible = OrganizationResponsible.objects.filter(
        organization=tender.organization,
        user=user
    ).exists()

    if not responsible:
        return Response({"reason": "User is not authorized to update the status of this tender."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TenderSerializer(tender, data=request.data, partial=True)
    if serializer.is_valid():
        TenderVersion.objects.create(
            tender_id=tender.id,
            name=tender.name,
            description=tender.description,
            service_type=tender.service_type,
            status=tender.status,
            organization_id=tender.organization.id,
            creator_username=tender.creator_username,
            created_at=tender.created_at,
            updated_at=tender.updated_at,
            version=tender.version
        )
        tender.version += 1
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([AllowAny])
def rollback_tender_version(request, tender_id, version):
    """
    Откатить параметры тендера к указанной версии.
    """
    username = request.GET.get('username')
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

    tender = get_object_or_404(Tender, id=tender_id)

    responsible = OrganizationResponsible.objects.filter(
        organization=tender.organization,
        user=user
    ).exists()

    if not responsible:
        return Response({"reason": "User is not authorized to update the status of this tender."}, status=status.HTTP_403_FORBIDDEN)

    try:
        tender_version = TenderVersion.objects.get(tender_id=tender_id, version=version)
    except TenderVersion.DoesNotExist:
        return Response({"reason": "Tender version with the specified version does not exist."}, status=status.HTTP_404_NOT_FOUND)

    tender.name = tender_version.name
    tender.description = tender_version.description
    tender.service_type = tender_version.service_type
    tender.status = tender_version.status
    tender.organization = tender_version.organization
    tender.creator_username = tender_version.creator_username
    tender.created_at = tender_version.created_at
    tender.updated_at = tender_version.updated_at
    tender.version = tender_version.version
    tender.save()

    # Удаление версии и всех более поздних версий
    TenderVersion.objects.filter(tender_id=tender_id, version__gte=version).delete()

    serializer = TenderSerializer(tender)
    return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["POST"])
@permission_classes([AllowAny])
def create_bid(request):
    """
    Создать новое предложение для существующего тендера
    """
    name = request.data.get('name')
    description = request.data.get('description')
    tender_id = request.data.get('tenderId')
    organization_id = request.data.get('organizationId')
    creator_username = request.data.get('creatorUsername')

    if not all([name, tender_id, organization_id, creator_username]):
        return Response({"reason": "Missing required fields: 'name', 'tenderId', 'organizationId', and/or 'creatorUsername'."}, status=status.HTTP_400_BAD_REQUEST)

    # Проверка существования создателя
    try:
        creator = Employee.objects.get(username=creator_username)
    except Employee.DoesNotExist:
        return Response({"reason": "Creator with the specified username does not exist."}, status=status.HTTP_400_BAD_REQUEST)

    # Проверка существования тендера
    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return Response({"reason": "Tender with the specified ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

    # Проверка существования организации
    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        return Response({"reason": "Organization with the specified ID does not exist."}, status=status.HTTP_400_BAD_REQUEST)

    tender_organization = Organization.objects.get(id=tender.organization.id)

    # Проверка, является ли создатель ответственным за организацию, связанную с тендером
    is_responsible = OrganizationResponsible.objects.filter(
        organization=tender_organization,
        user=creator
    ).exists()

    if is_responsible:
        return Response({"reason": "Creator cannot make bids for the organization related to the tender."}, status=status.HTTP_403_FORBIDDEN)

    # Создание нового предложения
    data = {
        'name': name,
        'description': description,
        'status': "CREATED",
        'tender': tender_id,
        'organization': organization_id,
        'creator_username': creator_username,
        'version': 1,
        'votes_for': 0
    }
    
    serializer = BidSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_bids(request):
    """
    Получение списка предложений для указанного пользователя по username.
    """
    username = request.GET.get('username')
    
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

    bids = Bid.objects.filter(creator_username=username)
    serializer = BidSerializer(bids, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_bids_for_tender(request, tender_id):
    """
    Получить список предложений для указанного тендера в зависимости от статуса и прав доступа
    с поддержкой пагинации через limit и offset.
    """
    tender = get_object_or_404(Tender, id=tender_id)
    
    username = request.GET.get('username')
    limit = request.GET.get('limit', 5)
    offset = request.GET.get('offset', 0)

    try:
        limit = int(limit)
        offset = int(offset)
    except ValueError:
        return Response({"reason": "Limit and offset must be integers."}, status=status.HTTP_400_BAD_REQUEST)

    if username:
        try:
            user = Employee.objects.get(username=username)
        except Employee.DoesNotExist:
            return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

        is_author = Bid.objects.filter(tender=tender, creator_username=username).exists()
        user_organization = OrganizationResponsible.objects.filter(user=user).first()
        is_responsible = user_organization and user_organization.organization == tender.organization

        if is_author or is_responsible:
            bids = Bid.objects.filter(tender=tender)
        else:
            bids = Bid.objects.filter(tender=tender, status='PUBLISHED')
    else:
        bids = Bid.objects.filter(tender=tender, status='PUBLISHED')

    paginated_bids = bids[offset:offset + limit]

    serializer = BidSerializer(paginated_bids, many=True)
    
    return Response(serializer.data, status=200)



@api_view(["GET", "PUT"])
@permission_classes([AllowAny])
def bid_status(request, bid_id):
    """
    В зависимости от метода запроса:
    - GET: Получить статус предложения.
    - PUT: Обновить статус предложения. Статус может обновлять автор предложения или ответственный за организацию.
    """
    username = request.data.get('username') if request.method == "PUT" else request.GET.get('username')
    
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        bid = Bid.objects.get(id=bid_id)
    except Bid.DoesNotExist:
        return Response({"reason": "Bid with the specified ID does not exist."}, status=status.HTTP_404_NOT_FOUND)

    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

    responsible = OrganizationResponsible.objects.filter(
        organization=bid.organization,
        user=user
    ).exists()

    author = (user.username == bid.creator_username)

    # GET-запрос: возвращаем текущий статус предложения
    if request.method == "GET":
        if responsible or author:
            return Response({"status": bid.status}, status=status.HTTP_200_OK)
        else:
            return Response({"reason": "User is not authorized to view the status of this bid."}, status=status.HTTP_403_FORBIDDEN)

    # PUT-запрос: обновляем статус предложения
    if request.method == "PUT":
        new_status = request.data.get('status')

        if not new_status:
            return Response({"reason": "Status is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        valid_statuses = ['PUBLISHED', 'CANCELED']
        if new_status not in valid_statuses:
            return Response({"reason": "Invalid status. Valid statuses are: 'PUBLISHED', 'CANCELED'."}, status=status.HTTP_400_BAD_REQUEST)

        if not responsible and not author:
            return Response({"reason": "User is not authorized to update the status of this bid."}, status=status.HTTP_403_FORBIDDEN)

        if bid.status != "CANCELED":
            bid.status = new_status
            bid.save()
        else:
            return Response({"reason": "You can't edit a canceled bid."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = BidSerializer(bid)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([AllowAny])
def submit_decision(request):
    """
    Отправка решения по предложению от ответственных за организацию, связанных с тендером.
    """
    decision = request.GET.get('decision')
    bid_id = request.GET.get('bidId')
    username = request.GET.get('username')

    if not decision:
        return Response({"reason": "Decision is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Проверка допустимых статусов
    valid_statuses = ['Accept', 'Decline']
    if decision not in valid_statuses:
        return Response({"reason": "Invalid status. Valid statuses are: 'Accept', 'Decline'."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        bid = Bid.objects.get(id=bid_id)
    except Bid.DoesNotExist:
        return Response({"reason": "Bid with the specified ID does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        tender = Tender.objects.get(id=bid.tender_id)
    except Tender.DoesNotExist:
        return Response({"reason": "Tender with the specified ID does not exist."}, status=status.HTTP_404_NOT_FOUND)

    responsible = OrganizationResponsible.objects.filter(
        organization=tender.organization,
        user=user
    ).exists()
    
    author = (user == bid.creator_username)

    if not responsible and not author:
        return Response({"reason": "User is not authorized to update the status of this bid."}, status=status.HTTP_403_FORBIDDEN)
    
    # Проверка, голосовал ли пользователь ранее
    if bid.voters.filter(id=user.id).exists():
        return Response({"reason": "User has already voted on this bid."}, status=status.HTTP_403_FORBIDDEN)

    # Обновление статуса предложения
    if decision == "Accept":
        bid.votes_for += 1
        bid.voters.add(user)
        bid.save()

        if bid.votes_for >= 3:
            tender.status = "CLOSED"  # Закрываем тендер
            tender.save()
    else:
        bid.status = "CANCELED"
        bid.save()
        return Response("That bid has been declined", status=status.HTTP_200_OK)

    serializer = BidSerializer(bid)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PATCH"])
@permission_classes([AllowAny])
def edit_bid(request, bid_id):
    """
    Редактирование предложения
    """
    username = request.GET.get('username')
    bid = get_object_or_404(Bid, id=bid_id)
    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
    responsible = OrganizationResponsible.objects.filter(
        organization=bid.organization,
        user=user
    ).exists()

    author = (user == bid.creator_username)

    if not responsible and not author:
        return Response({"reason": "User is not authorized to update the status of this bid."}, status=status.HTTP_403_FORBIDDEN)

    serializer = BidSerializer(bid, data=request.data, partial=True)

    if serializer.is_valid():
        # Сохранение текущей версии предложения в таблице версий перед изменением
        BidVersion.objects.create(
            bid_id=bid.id,
            name=bid.name,
            description=bid.description,
            status=bid.status,
            tender_id=bid.tender.id,
            organization_id=bid.organization.id,
            creator_username=bid.creator_username,
            created_at=bid.created_at,
            updated_at=bid.updated_at,
            version=bid.version,
            votes_for=bid.votes_for,
        )
        bid.version += 1
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(["PUT"])
@permission_classes([AllowAny])
def rollback_bid_version(request, bid_id, version):
    """
    Откатить параметры предложения к указанной версии.
    """
    username = request.GET.get('username')

    if not username:
        return Response({"reason": "Username is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        bid = Bid.objects.get(id=bid_id)
    except Bid.DoesNotExist:
        return Response({"reason": "Bid with the specified ID does not exist."}, status=status.HTTP_404_NOT_FOUND)

    responsible = OrganizationResponsible.objects.filter(
        organization=bid.organization,
        user=user
    ).exists()
    
    author = (user == bid.creator_username)

    if not responsible and not author:
        return Response({"reason": "User is not authorized to update or rollback the status of this bid."}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        bid_version = BidVersion.objects.get(bid_id=bid_id, version=version)
    except BidVersion.DoesNotExist:
        return Response({"reason": "Bid version with the specified version does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
    # Обновление текущего предложения данными из указанной версии
    bid.name = bid_version.name
    bid.description = bid_version.description
    bid.status = bid_version.status
    bid.tender = bid_version.tender
    bid.organization = bid_version.organization
    bid.creator_username = bid_version.creator_username
    bid.created_at = bid_version.created_at
    bid.updated_at = bid_version.updated_at
    bid.version = bid_version.version
    bid.votes_for = bid_version.votes_for
    bid.save()

    # Удаление всех версий, которые равны или превышают текущую откатываемую версию
    BidVersion.objects.filter(bid_id=bid_id, version__gte=version).delete()

    serializer = BidSerializer(bid)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([AllowAny])
def create_review(request, bid_id):
    """
    Оставление отзыва на предложение
    """
    username = request.GET.get('username')
    content = request.GET.get('bidFeedback')

    if not username or not content:
        return Response({"reason": "Username and content are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Employee.objects.get(username=username)
    except Employee.DoesNotExist:
        return Response({"reason": "User with the specified username does not exist."}, status=status.HTTP_404_NOT_FOUND)

    bid = get_object_or_404(Bid, id=bid_id)
    
    responsible = OrganizationResponsible.objects.filter(
        organization=bid.organization,
        user=user
    ).exists()

    if not responsible:
        return Response({"reason": "User is not authorized to leave a review for this bid."}, status=status.HTTP_403_FORBIDDEN)

    review = Review.objects.create(
        bid=bid,
        user=user,
        content=content
    )

    serializer = ReviewSerializer(review)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_reviews(request, tender_id):
    """
    Просмотр отзывов на предложения автора.
    """
    author_username = request.GET.get('authorUsername')
    request_username = request.GET.get('requestUsername')

    limit = int(request.GET.get('limit', 5))
    offset = int(request.GET.get('offset', 0))

    if not author_username or not request_username:
        return Response({"reason": "username are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        author = Employee.objects.get(username=author_username)
    except Employee.DoesNotExist:
        return Response({"reason": "Author with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        user = Employee.objects.get(username=request_username)
    except Employee.DoesNotExist:
        return Response({"reason": "Request User with the specified username does not exist."}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        tender = Tender.objects.get(id=tender_id)
    except Tender.DoesNotExist:
        return Response({"reason": "Tender with the specified ID does not exist."}, status=status.HTTP_404_NOT_FOUND)

    bids = Bid.objects.filter(
        tender_id=tender_id,
        creator_username=author
    )

    responsible = OrganizationResponsible.objects.filter(
        organization=tender.organization,
        user=user
    ).exists()

    if not responsible:
        return Response({"reason": "User is not authorized to view reviews for this tender."}, status=status.HTTP_403_FORBIDDEN)

    reviews = Review.objects.filter(bid__in=bids)[offset:offset + limit]
    serializer = ReviewSerializer(reviews, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)
