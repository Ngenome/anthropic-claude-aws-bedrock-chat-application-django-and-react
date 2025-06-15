from rest_framework import serializers
from .models import DesignProject, Group, Prototype, PrototypeVariant, PrototypeVersion

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class PrototypeVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PrototypeVersion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'version_number', 'html_content']

class PrototypeVariantSerializer(serializers.ModelSerializer):
    latest_version = serializers.SerializerMethodField()
    versions_count = serializers.SerializerMethodField()
    versions = PrototypeVersionSerializer(many=True, read_only=True)
    
    class Meta:
        model = PrototypeVariant
        fields = ['id', 'prototype', 'name', 'description', 'is_original', 
                 'created_at', 'updated_at', 'latest_version', 'versions_count', 'versions']
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_original']
    
    def get_latest_version(self, obj):
        latest = obj.versions.order_by('-version_number').first()
        if latest:
            return PrototypeVersionSerializer(latest).data
        return None
    
    def get_versions_count(self, obj):
        return obj.versions.count()

class PrototypeVariantDetailSerializer(PrototypeVariantSerializer):
    versions = PrototypeVersionSerializer(many=True, read_only=True)
    
    class Meta(PrototypeVariantSerializer.Meta):
        fields = PrototypeVariantSerializer.Meta.fields + ['versions']

class PrototypeSerializer(serializers.ModelSerializer):
    variants_count = serializers.SerializerMethodField()
    original_variant = serializers.SerializerMethodField()
    
    class Meta:
        model = Prototype
        fields = ['id', 'design_project', 'group', 'title', 'prompt', 
                 'created_at', 'updated_at', 'variants_count', 'original_variant']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_variants_count(self, obj):
        return obj.variants.count()
    
    def get_original_variant(self, obj):
        original = obj.variants.filter(is_original=True).first()
        if original:
            return PrototypeVariantSerializer(original).data
        return None

class PrototypeDetailSerializer(PrototypeSerializer):
    variants = PrototypeVariantSerializer(many=True, read_only=True)
    
    class Meta(PrototypeSerializer.Meta):
        fields = PrototypeSerializer.Meta.fields + ['variants']

class DesignProjectSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    prototypes_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DesignProject
        fields = ['id', 'user', 'title', 'description', 'created_at', 'updated_at', 
                 'groups', 'prototypes_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']
    
    def get_prototypes_count(self, obj):
        return obj.prototypes.count()

class DesignProjectDetailSerializer(DesignProjectSerializer):
    prototypes = PrototypeSerializer(many=True, read_only=True)
    
    class Meta(DesignProjectSerializer.Meta):
        fields = DesignProjectSerializer.Meta.fields + ['prototypes'] 