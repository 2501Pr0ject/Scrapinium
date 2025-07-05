"""Router pour les endpoints de templates de scraping."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query

from ...models.schemas import (
    APIResponse, 
    ScrapingTemplateCreate, 
    ScrapingTemplateResponse,
    ScrapingTemplateUpdate,
    ScrapingWithTemplateRequest
)
from ...utils.logging import get_logger
from ..services.template_service import get_template_service
from ..services.scraping_service import get_scraping_task_service

logger = get_logger("templates_router")

router = APIRouter(
    prefix="/templates",
    tags=["templates"]
)


@router.post("", response_model=APIResponse)
async def create_template(template_data: ScrapingTemplateCreate):
    """Créer un nouveau template de scraping."""
    try:
        template_service = get_template_service()
        template = template_service.create_template(template_data)
        
        return APIResponse.success_response(
            data=template.dict(),
            message=f"Template '{template.name}' créé avec succès"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur création template: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la création du template"
        )


@router.get("", response_model=APIResponse)
async def list_templates(
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    tags: Optional[List[str]] = Query(None, description="Filtrer par tags"),
    search: Optional[str] = Query(None, description="Recherche textuelle"),
    limit: int = Query(20, ge=1, le=100, description="Nombre de résultats"),
    offset: int = Query(0, ge=0, description="Décalage pour pagination"),
    public_only: bool = Query(True, description="Seulement les templates publics")
):
    """Lister les templates de scraping avec filtrage."""
    try:
        template_service = get_template_service()
        templates = template_service.list_templates(
            category=category,
            tags=tags,
            search=search,
            limit=limit,
            offset=offset,
            public_only=public_only
        )
        
        return APIResponse.success_response(
            data={
                "templates": [t.dict() for t in templates],
                "total": len(templates),
                "limit": limit,
                "offset": offset
            },
            message="Templates récupérés avec succès"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur listage templates: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la récupération des templates"
        )


@router.get("/categories", response_model=APIResponse)
async def get_template_categories():
    """Récupérer les catégories de templates disponibles."""
    try:
        template_service = get_template_service()
        categories = template_service.get_template_categories()
        
        return APIResponse.success_response(
            data={"categories": categories},
            message="Catégories récupérées avec succès"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération catégories: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la récupération des catégories"
        )


@router.get("/popular", response_model=APIResponse)
async def get_popular_templates(
    limit: int = Query(10, ge=1, le=50, description="Nombre de templates populaires")
):
    """Récupérer les templates les plus populaires."""
    try:
        template_service = get_template_service()
        templates = template_service.get_popular_templates(limit=limit)
        
        return APIResponse.success_response(
            data={
                "templates": [t.dict() for t in templates],
                "total": len(templates)
            },
            message="Templates populaires récupérés"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération templates populaires: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la récupération des templates populaires"
        )


@router.get("/{template_id}", response_model=APIResponse)
async def get_template(template_id: int):
    """Récupérer un template spécifique."""
    try:
        template_service = get_template_service()
        template = template_service.get_template_by_id(template_id)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} non trouvé"
            )
        
        return APIResponse.success_response(
            data=template.dict(),
            message="Template récupéré avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur récupération template {template_id}: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la récupération du template"
        )


@router.put("/{template_id}", response_model=APIResponse)
async def update_template(template_id: int, update_data: ScrapingTemplateUpdate):
    """Mettre à jour un template."""
    try:
        template_service = get_template_service()
        template = template_service.update_template(template_id, update_data)
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} non trouvé"
            )
        
        return APIResponse.success_response(
            data=template.dict(),
            message="Template mis à jour avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour template {template_id}: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la mise à jour du template"
        )


@router.delete("/{template_id}", response_model=APIResponse)
async def delete_template(template_id: int):
    """Supprimer un template."""
    try:
        template_service = get_template_service()
        success = template_service.delete_template(template_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Template {template_id} non trouvé"
            )
        
        return APIResponse.success_response(
            data={"template_id": template_id, "deleted": True},
            message="Template supprimé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur suppression template {template_id}: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la suppression du template"
        )


@router.post("/scrape", response_model=APIResponse)
async def scrape_with_template(
    template_request: ScrapingWithTemplateRequest,
    background_tasks: BackgroundTasks
):
    """Créer une tâche de scraping en utilisant un template."""
    try:
        template_service = get_template_service()
        scraping_service = get_scraping_task_service()
        
        # Créer la tâche de scraping à partir du template
        scraping_task = template_service.create_scraping_task_from_template(template_request)
        
        # Créer et lancer la tâche
        task_id = scraping_service.create_task(scraping_task)
        
        # Lancer la tâche en arrière-plan
        background_tasks.add_task(
            scraping_service.execute_task,
            task_id,
            scraping_task
        )
        
        return APIResponse.success_response(
            data={
                "task_id": task_id,
                "template_id": template_request.template_id,
                "url": str(template_request.url),
                "status": "pending"
            },
            message="Scraping avec template démarré"
        )
        
    except ValueError as e:
        logger.warning(f"⚠️ Erreur validation template: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Template non valide"
        )
    except Exception as e:
        logger.error(f"❌ Erreur scraping avec template: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors du scraping avec template"
        )


# === ENDPOINTS ADMINISTRATEUR ===

@router.post("/seed", response_model=APIResponse)
async def seed_default_templates():
    """Créer les templates par défaut (admin seulement)."""
    try:
        template_service = get_template_service()
        
        # Templates par défaut
        default_templates = [
            ScrapingTemplateCreate(
                name="Article de blog",
                description="Extraction d'articles de blog avec titre, contenu et métadonnées",
                category="blog",
                instructions="""Extraire le contenu principal de cet article de blog. Inclure:
- Le titre principal
- L'auteur si disponible
- La date de publication
- Le contenu de l'article complet
- Les tags/catégories
Formater en markdown structuré.""",
                example_urls=["https://example-blog.com/article"],
                tags=["article", "blog", "contenu"],
                css_selectors={
                    "title": "h1, .article-title, .post-title",
                    "content": ".article-content, .post-content, main article",
                    "author": ".author, .byline, .post-author",
                    "date": ".date, .published, .post-date"
                }
            ),
            ScrapingTemplateCreate(
                name="Produit e-commerce",
                description="Extraction de données produit: prix, description, avis",
                category="ecommerce",
                instructions="""Extraire les informations produit suivantes:
- Nom du produit
- Prix actuel et ancien prix si disponible
- Description détaillée
- Caractéristiques techniques
- Note moyenne et nombre d'avis
- Images principales
- Disponibilité en stock
Formater les données en JSON structuré.""",
                example_urls=["https://example-shop.com/product/123"],
                tags=["ecommerce", "produit", "prix", "avis"],
                css_selectors={
                    "name": "h1, .product-name, .product-title",
                    "price": ".price, .current-price, .product-price",
                    "description": ".description, .product-description",
                    "rating": ".rating, .stars, .review-rating"
                }
            ),
            ScrapingTemplateCreate(
                name="Article de presse",
                description="Extraction d'articles de journaux et sites d'actualités",
                category="news",
                instructions="""Extraire l'article de presse avec:
- Titre principal et sous-titre
- Journaliste/auteur
- Date et heure de publication
- Chapô/résumé
- Corps de l'article complet
- Citations importantes
- Source et crédits
Conserver la structure journalistique.""",
                example_urls=["https://example-news.com/article/123"],
                tags=["news", "presse", "actualité"],
                css_selectors={
                    "headline": "h1, .headline, .article-headline",
                    "byline": ".byline, .author, .journalist",
                    "content": ".article-body, .content, .story-content",
                    "date": ".date, .timestamp, .publication-date"
                }
            ),
            ScrapingTemplateCreate(
                name="Recherche académique",
                description="Extraction de publications scientifiques et recherches",
                category="academic",
                instructions="""Extraire les informations académiques:
- Titre de la publication
- Auteurs et affiliations
- Résumé/abstract
- Introduction
- Méthodologie si disponible
- Conclusion/résultats
- Références bibliographiques
- DOI et métadonnées
Maintenir la rigueur académique.""",
                example_urls=["https://example-journal.com/paper/123"],
                tags=["académique", "recherche", "science"],
                css_selectors={
                    "title": "h1, .article-title, .paper-title",
                    "authors": ".authors, .author-list",
                    "abstract": ".abstract, .summary",
                    "content": ".article-content, .paper-content"
                }
            ),
            ScrapingTemplateCreate(
                name="Immobilier",
                description="Extraction d'annonces immobilières",
                category="real-estate",
                instructions="""Extraire les données immobilières:
- Type de bien (appartement, maison, etc.)
- Prix de vente ou loyer
- Surface et nombre de pièces
- Localisation précise
- Description du bien
- Caractéristiques (balcon, parking, etc.)
- Contact de l'agence
- Photos disponibles
Structurer les données pour comparaison.""",
                example_urls=["https://example-realestate.com/property/123"],
                tags=["immobilier", "logement", "prix"],
                css_selectors={
                    "price": ".price, .property-price",
                    "surface": ".surface, .size, .area",
                    "location": ".location, .address",
                    "description": ".description, .property-description"
                }
            )
        ]
        
        created_templates = []
        for template_data in default_templates:
            try:
                template = template_service.create_template(template_data)
                created_templates.append(template.name)
            except Exception as e:
                logger.warning(f"⚠️ Template '{template_data.name}' existe déjà ou erreur: {e}")
        
        return APIResponse.success_response(
            data={
                "created_templates": created_templates,
                "total_created": len(created_templates)
            },
            message=f"{len(created_templates)} templates par défaut créés"
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur création templates par défaut: {e}")
        return APIResponse.error_response(
            errors=[str(e)],
            message="Erreur lors de la création des templates par défaut"
        )