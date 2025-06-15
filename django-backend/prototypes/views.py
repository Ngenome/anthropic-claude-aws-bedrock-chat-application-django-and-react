from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import DesignProject, Group, Prototype, PrototypeVariant, PrototypeVersion
from .serializers import (
    DesignProjectSerializer, DesignProjectDetailSerializer,
    GroupSerializer, 
    PrototypeSerializer, PrototypeDetailSerializer,
    PrototypeVariantSerializer, PrototypeVariantDetailSerializer,
    PrototypeVersionSerializer
)
from .services import PrototypeService

# Create your views here.

class DesignProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DesignProject.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DesignProjectDetailSerializer
        return DesignProjectSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Group.objects.filter(design_project__user=self.request.user)
    
    def perform_create(self, serializer):
        design_project = get_object_or_404(
            DesignProject, 
            id=self.request.data.get('design_project'),
            user=self.request.user
        )
        serializer.save(design_project=design_project)

class PrototypeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Prototype.objects.filter(design_project__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PrototypeDetailSerializer
        return PrototypeSerializer

    @action(detail=True, methods=['post'])
    def create_variant(self, request, pk=None):
        """Create a new variant for a prototype"""
        prototype = self.get_object()
        variant_name = request.data.get('name', f"Variant of {prototype.title}")
        variant_description = request.data.get('description', '')
        variant_prompt = request.data.get('prompt', None)
        
        # Get the original variant to use as a base
        original_variant = prototype.variants.filter(is_original=True).first()
        
        if not original_variant:
            return Response(
                {'error': 'No original variant found for this prototype'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the latest version of the original variant
        base_version = original_variant.versions.order_by('-version_number').first()
        
        if not base_version:
            return Response(
                {'error': 'No versions found for the original variant'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create the new variant
            new_variant = PrototypeVariant.objects.create(
                prototype=prototype,
                name=variant_name,
                description=variant_description,
                is_original=False
            )
            
            # Generate the variant using Claude
            prototype_service = PrototypeService()
            result = prototype_service.create_variant(
                base_version.html_content, 
                variant_prompt
            )
            
            # Create the first version (version 0) for this variant
            version = PrototypeVersion.objects.create(
                variant=new_variant,
                version_number=0,
                name=result['name'],
                edit_prompt=variant_prompt,
                html_content=result['html_content']
            )
            
            # Return the new variant with its first version
            variant_serializer = PrototypeVariantDetailSerializer(new_variant)
            return Response(variant_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PrototypeVariantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PrototypeVariant.objects.filter(prototype__design_project__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PrototypeVariantDetailSerializer
        return PrototypeVariantSerializer
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Create a new version for a variant by editing the previous version"""
        variant = self.get_object()
        edit_prompt = request.data.get('edit_prompt')
        version_name = request.data.get('name', 'Updated Version')
        
        if not edit_prompt:
            return Response(
                {'error': 'Edit prompt is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the latest version to edit
        latest_version = variant.versions.order_by('-version_number').first()
        
        if not latest_version:
            return Response(
                {'error': 'No previous versions found for this variant'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generate the edited version
            prototype_service = PrototypeService()
            result = prototype_service.edit_prototype(
                latest_version.html_content, 
                edit_prompt
            )
            
            # Create the new version with incremented version number
            new_version = PrototypeVersion.objects.create(
                variant=variant,
                version_number=latest_version.version_number + 1,
                name=result['name'],
                edit_prompt=edit_prompt,
                html_content=result['html_content']
            )
            
            # Return the new version
            serializer = PrototypeVersionSerializer(new_version)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PrototypeVersionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PrototypeVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PrototypeVersion.objects.filter(variant__prototype__design_project__user=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def design_project_prototypes(request, project_id):
    """Get all prototypes for a specific design project"""
    design_project = get_object_or_404(DesignProject, id=project_id, user=request.user)
    prototypes = Prototype.objects.filter(design_project=design_project)
    serializer = PrototypeSerializer(prototypes, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_prototypes(request, group_id):
    """Get all prototypes for a specific group"""
    group = get_object_or_404(Group, id=group_id, design_project__user=request.user)
    prototypes = Prototype.objects.filter(group=group)
    serializer = PrototypeSerializer(prototypes, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_prototype(request):
    """Generate a new prototype using AI"""
    # Get the design project
    design_project_id = request.data.get('design_project_id')
    design_project = get_object_or_404(DesignProject, id=design_project_id, user=request.user)
    
    # Get prompt and optional group
    prompt = request.data.get('prompt')
    group_id = request.data.get('group_id', None)
    
    if not prompt:
        return Response({'error': 'Prompt is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Set up group if provided
    group = None
    if group_id:
        group = get_object_or_404(Group, id=group_id, design_project=design_project)
    
    # Generate prototype using AI
    try:
        prototype_service = PrototypeService()
        result = prototype_service.generate_prototype(prompt)
        
        # Create and save the prototype
        prototype = Prototype.objects.create(
            design_project=design_project,
            group=group,
            title=result['name'],
            prompt=prompt
        )
        
        # Create the original variant
        variant = PrototypeVariant.objects.create(
            prototype=prototype,
            name="Original",
            description="Original prototype design",
            is_original=True
        )
        
        # Create the first version (version 0)
        version = PrototypeVersion.objects.create(
            variant=variant,
            version_number=0,
            name=result['name'],
            html_content=result['html_content']
        )
        
        # Return the created prototype with its variant and version
        serializer = PrototypeDetailSerializer(prototype)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
