"""Service de gestion des templates de scraping."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ...config.database import db_manager
from ...models.database import ScrapingTemplate
from ...models.schemas import (
    ScrapingTemplateCreate,
    ScrapingTemplateResponse,
    ScrapingTemplateUpdate,
    ScrapingWithTemplateRequest,
    ScrapingTaskCreate
)
from ...utils.logging import get_logger

logger = get_logger("template_service")


class TemplateService:
    """Service pour gérer les templates de scraping."""

    def __init__(self):
        self.db = db_manager.get_sync_session()

    def create_template(self, template_data: ScrapingTemplateCreate) -> ScrapingTemplateResponse:
        """Créer un nouveau template de scraping."""
        try:
            logger.info(f"🏗️ Création template: {template_data.name}")
            
            # Créer le template
            template = ScrapingTemplate(
                template_id=str(uuid.uuid4()),
                name=template_data.name,
                description=template_data.description,
                category=template_data.category,
                output_format=template_data.output_format.value,
                llm_provider=template_data.llm_provider.value,
                llm_model=template_data.llm_model,
                instructions=template_data.instructions,
                example_urls=template_data.example_urls,
                css_selectors=template_data.css_selectors,
                is_public=template_data.is_public,
                tags=template_data.tags,
                usage_count=0
            )
            
            # Sauvegarder en base
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"✅ Template créé: {template.id}")
            
            return self._template_to_response(template)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erreur création template: {e}")
            raise

    def get_template_by_id(self, template_id: int) -> Optional[ScrapingTemplateResponse]:
        """Récupérer un template par ID."""
        try:
            template = self.db.query(ScrapingTemplate).filter(
                and_(
                    ScrapingTemplate.id == template_id,
                    ScrapingTemplate.is_active == True
                )
            ).first()
            
            if not template:
                return None
            
            return self._template_to_response(template)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération template {template_id}: {e}")
            raise

    def list_templates(
        self, 
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        public_only: bool = True
    ) -> List[ScrapingTemplateResponse]:
        """Lister les templates avec filtrage."""
        try:
            query = self.db.query(ScrapingTemplate).filter(
                ScrapingTemplate.is_active == True
            )
            
            # Filtre public
            if public_only:
                query = query.filter(ScrapingTemplate.is_public == True)
            
            # Filtre par catégorie
            if category:
                query = query.filter(ScrapingTemplate.category == category)
            
            # Filtre par tags
            if tags:
                for tag in tags:
                    query = query.filter(
                        ScrapingTemplate.tags.contains([tag])
                    )
            
            # Recherche textuelle
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        ScrapingTemplate.name.like(search_pattern),
                        ScrapingTemplate.description.like(search_pattern),
                        ScrapingTemplate.instructions.like(search_pattern)
                    )
                )
            
            # Tri et pagination
            templates = query.order_by(
                desc(ScrapingTemplate.usage_count),
                desc(ScrapingTemplate.created_at)
            ).offset(offset).limit(limit).all()
            
            return [self._template_to_response(t) for t in templates]
            
        except Exception as e:
            logger.error(f"❌ Erreur listage templates: {e}")
            raise

    def get_template_categories(self) -> List[Dict[str, Any]]:
        """Récupérer les catégories de templates avec compteurs."""
        try:
            categories = self.db.query(
                ScrapingTemplate.category,
                func.count(ScrapingTemplate.id).label('count')
            ).filter(
                and_(
                    ScrapingTemplate.is_active == True,
                    ScrapingTemplate.is_public == True
                )
            ).group_by(ScrapingTemplate.category).all()
            
            return [
                {"category": cat.category, "count": cat.count}
                for cat in categories
            ]
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération catégories: {e}")
            raise

    def get_popular_templates(self, limit: int = 10) -> List[ScrapingTemplateResponse]:
        """Récupérer les templates les plus populaires."""
        try:
            templates = self.db.query(ScrapingTemplate).filter(
                and_(
                    ScrapingTemplate.is_active == True,
                    ScrapingTemplate.is_public == True
                )
            ).order_by(
                desc(ScrapingTemplate.usage_count)
            ).limit(limit).all()
            
            return [self._template_to_response(t) for t in templates]
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération templates populaires: {e}")
            raise

    def update_template(self, template_id: int, update_data: ScrapingTemplateUpdate) -> Optional[ScrapingTemplateResponse]:
        """Mettre à jour un template."""
        try:
            template = self.db.query(ScrapingTemplate).filter(
                and_(
                    ScrapingTemplate.id == template_id,
                    ScrapingTemplate.is_active == True
                )
            ).first()
            
            if not template:
                return None
            
            # Mettre à jour les champs modifiés
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if hasattr(template, field):
                    setattr(template, field, value)
            
            template.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(template)
            
            logger.info(f"✅ Template {template_id} mis à jour")
            
            return self._template_to_response(template)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erreur mise à jour template {template_id}: {e}")
            raise

    def delete_template(self, template_id: int) -> bool:
        """Supprimer un template (soft delete)."""
        try:
            template = self.db.query(ScrapingTemplate).filter(
                ScrapingTemplate.id == template_id
            ).first()
            
            if not template:
                return False
            
            # Soft delete
            template.is_active = False
            template.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"✅ Template {template_id} supprimé")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Erreur suppression template {template_id}: {e}")
            raise

    def increment_usage(self, template_id: int) -> None:
        """Incrémenter le compteur d'utilisation d'un template."""
        try:
            template = self.db.query(ScrapingTemplate).filter(
                ScrapingTemplate.id == template_id
            ).first()
            
            if template:
                template.usage_count += 1
                template.updated_at = datetime.utcnow()
                self.db.commit()
                
        except Exception as e:
            logger.error(f"❌ Erreur incrémentation usage template {template_id}: {e}")

    def create_scraping_task_from_template(
        self, 
        template_request: ScrapingWithTemplateRequest
    ) -> ScrapingTaskCreate:
        """Créer une tâche de scraping à partir d'un template."""
        try:
            # Récupérer le template
            template = self.db.query(ScrapingTemplate).filter(
                and_(
                    ScrapingTemplate.id == template_request.template_id,
                    ScrapingTemplate.is_active == True
                )
            ).first()
            
            if not template:
                raise ValueError(f"Template {template_request.template_id} non trouvé")
            
            # Incrémenter le compteur d'usage
            self.increment_usage(template_request.template_id)
            
            # Combiner instructions du template et instructions personnalisées
            instructions = template.instructions
            if template_request.custom_instructions:
                instructions += f"\n\nInstructions personnalisées:\n{template_request.custom_instructions}"
            
            # Créer la tâche de scraping
            scraping_task = ScrapingTaskCreate(
                url=template_request.url,
                output_format=template_request.override_format or template.output_format,
                llm_provider=template.llm_provider,
                llm_model=template.llm_model,
                custom_instructions=instructions
            )
            
            logger.info(f"✅ Tâche créée avec template {template.name}")
            
            return scraping_task
            
        except Exception as e:
            logger.error(f"❌ Erreur création tâche avec template: {e}")
            raise

    def _template_to_response(self, template: ScrapingTemplate) -> ScrapingTemplateResponse:
        """Convertir un modèle template en réponse."""
        return ScrapingTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            output_format=template.output_format,
            llm_provider=template.llm_provider,
            llm_model=template.llm_model,
            instructions=template.instructions,
            example_urls=template.example_urls or [],
            css_selectors=template.css_selectors,
            is_public=template.is_public,
            tags=template.tags or [],
            usage_count=template.usage_count,
            created_at=template.created_at,
            updated_at=template.updated_at,
            author=template.author
        )


# Instance singleton
_template_service_instance = None


def get_template_service() -> TemplateService:
    """Récupérer l'instance du service template."""
    global _template_service_instance
    if _template_service_instance is None:
        _template_service_instance = TemplateService()
    return _template_service_instance