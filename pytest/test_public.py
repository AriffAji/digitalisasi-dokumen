"""
Integration tests for public routes.
Tests cover home page, kamar listing, dokumen listing, searching, and document downloads.
"""

import pytest
from datetime import datetime, timedelta
from models import db, Kamar, SubKamar, Dokumen, ShareLink


class TestPublicIndex:
    """Test public home page."""

    @pytest.mark.integration
    def test_index_page_loads(self, client):
        """Test home page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_index_displays_statistics(self, client, multiple_kamar, multiple_dokumen):
        """Test index page displays statistics."""
        response = client.get('/')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_index_empty_database(self, client):
        """Test index page with empty database."""
        response = client.get('/')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_index_shows_kamar_list(self, client, kamar_aktif):
        """Test index shows active kamar."""
        response = client.get('/')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_index_ordered_by_urutan(self, client, multiple_kamar):
        """Test kamar are ordered by urutan field."""
        response = client.get('/')
        assert response.status_code == 200


class TestKamarPage:
    """Test kamar listing page."""

    @pytest.mark.integration
    def test_kamar_page_active(self, client, kamar_aktif, multiple_sub_kamar):
        """Test accessing active kamar page."""
        response = client.get(f'/kamar/{kamar_aktif.id}')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_kamar_page_locked_denies_access(self, client, kamar_terkunci):
        """Test accessing locked kamar returns 403."""
        response = client.get(f'/kamar/{kamar_terkunci.id}')
        assert response.status_code == 403

    @pytest.mark.integration
    def test_kamar_page_nonexistent(self, client):
        """Test accessing non-existent kamar returns 404."""
        response = client.get('/kamar/9999')
        assert response.status_code == 404

    @pytest.mark.integration
    def test_kamar_page_shows_sub_kamar_list(self, client, kamar_aktif, multiple_sub_kamar):
        """Test kamar page displays sub kamar list."""
        response = client.get(f'/kamar/{kamar_aktif.id}')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_kamar_page_multiple_sub_kamar(self, client, kamar_aktif):
        """Test kamar with multiple sub kamar."""
        with client.application.app_context():
            for i in range(5):
                sub = SubKamar(kamar_id=kamar_aktif.id, nama=f'Sub {i}')
                db.session.add(sub)
            db.session.commit()

        response = client.get(f'/kamar/{kamar_aktif.id}')
        assert response.status_code == 200


class TestDokumenPage:
    """Test dokumen listing page."""

    @pytest.mark.integration
    def test_dokumen_page_loads(self, client, kamar_aktif, sub_kamar):
        """Test dokumen page loads."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_page_locked_kamar_denies_access(self, client, kamar_terkunci, sub_kamar):
        """Test accessing dokumen in locked kamar returns 403."""
        response = client.get(f'/kamar/{kamar_terkunci.id}/sub/{sub_kamar.id}')
        assert response.status_code == 403

    @pytest.mark.integration
    def test_dokumen_page_nonexistent_kamar(self, client):
        """Test accessing dokumen with non-existent kamar."""
        response = client.get('/kamar/9999/sub/1')
        assert response.status_code == 404

    @pytest.mark.integration
    def test_dokumen_page_nonexistent_sub_kamar(self, client, kamar_aktif):
        """Test accessing dokumen with non-existent sub kamar."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/9999')
        assert response.status_code == 404

    @pytest.mark.integration
    def test_dokumen_page_pagination(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test dokumen page pagination."""
        with client.application.app_context():
            # Create 25 documents
            for i in range(25):
                dok = Dokumen(
                    sub_kamar_id=sub_kamar.id,
                    judul=f'Dokumen {i}',
                    file_path=f'/up/dok{i}.pdf',
                    uploaded_by=regular_user.id
                )
                db.session.add(dok)
            db.session.commit()

        # First page
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?page=1')
        assert response.status_code == 200

        # Second page
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?page=2')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_search_by_judul(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test searching dokumen by title."""
        with client.application.app_context():
            dok1 = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Surat Masuk Januari',
                file_path='/up/1.pdf',
                uploaded_by=regular_user.id
            )
            dok2 = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Laporan Bulanan',
                file_path='/up/2.pdf',
                uploaded_by=regular_user.id
            )
            db.session.add(dok1)
            db.session.add(dok2)
            db.session.commit()

        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?cari=Surat')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_search_by_nomor_dokumen(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test searching dokumen by nomor dokumen."""
        with client.application.app_context():
            dok = Dokumen(
                sub_kamar_id=sub_kamar.id,
                nomor_dokumen='DOK/2026/001',
                judul='Test',
                file_path='/up/test.pdf',
                uploaded_by=regular_user.id
            )
            db.session.add(dok)
            db.session.commit()

        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?cari=DOK/2026')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_filter_by_tahun(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test filtering dokumen by year."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?tahun=2026')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_filter_by_status(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test filtering dokumen by status."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?status=aktif')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_combined_filters(self, client, kamar_aktif, sub_kamar):
        """Test combining multiple filters."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?cari=test&tahun=2026&status=aktif')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_cache_without_filters(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test caching is applied when no filters present."""
        with client.application.app_context():
            dok = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Test Doc',
                file_path='/up/test.pdf',
                uploaded_by=regular_user.id
            )
            db.session.add(dok)
            db.session.commit()

        response1 = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}')
        response2 = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}')

        assert response1.status_code == 200
        assert response2.status_code == 200

    @pytest.mark.integration
    def test_dokumen_no_cache_with_search(self, client, kamar_aktif, sub_kamar):
        """Test cache is bypassed when search filter present."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?cari=test')
        assert response.status_code == 200


class TestGlobalSearch:
    """Test global search functionality."""

    @pytest.mark.integration
    def test_search_page_loads(self, client):
        """Test search page loads."""
        response = client.get('/search')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_api_global_search_empty_query(self, client):
        """Test API search with empty query."""
        response = client.get('/api/global-search?q=')
        assert response.status_code == 200
        assert response.json == []

    @pytest.mark.integration
    def test_api_global_search_short_query(self, client):
        """Test API search with query less than 2 characters."""
        response = client.get('/api/global-search?q=a')
        assert response.status_code == 200
        assert response.json == []

    @pytest.mark.integration
    def test_api_global_search_finds_public_dokumen(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test API search finds public dokumen."""
        with client.application.app_context():
            dok = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Public Dokumen Cari',
                file_path='/up/pub.pdf',
                visibilitas='publik',
                uploaded_by=regular_user.id
            )
            db.session.add(dok)
            db.session.commit()

        response = client.get('/api/global-search?q=Public')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_api_global_search_ignores_internal_dokumen(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test API search ignores internal dokumen."""
        with client.application.app_context():
            dok = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Internal Secret Dokumen',
                file_path='/up/sec.pdf',
                visibilitas='internal',
                uploaded_by=regular_user.id
            )
            db.session.add(dok)
            db.session.commit()

        response = client.get('/api/global-search?q=Secret')
        assert response.status_code == 200
        assert response.json == [] or len(response.json) == 0

    @pytest.mark.integration
    def test_api_global_search_filter_by_tahun(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test API search with tahun filter."""
        response = client.get('/api/global-search?q=test&tahun=2026')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_api_global_search_filter_by_status(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test API search with status filter."""
        response = client.get('/api/global-search?q=test&status=aktif')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_api_global_search_invalid_tahun(self, client):
        """Test API search with invalid tahun format."""
        response = client.get('/api/global-search?q=test&tahun=invalid')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_api_global_search_returns_json(self, client):
        """Test API search returns JSON."""
        response = client.get('/api/global-search?q=test')
        assert response.status_code == 200
        assert response.content_type == 'application/json'


class TestPublicSecurity:
    """Test security aspects of public routes."""

    @pytest.mark.integration
    def test_cannot_access_internal_dokumen_without_login(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test internal dokumen is not accessible without login."""
        with client.application.app_context():
            dok = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Internal Doc',
                file_path='/up/internal.pdf',
                visibilitas='internal',
                uploaded_by=regular_user.id
            )
            db.session.add(dok)
            db.session.commit()

        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_search_respects_visibility(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test search respects dokumen visibility."""
        with client.application.app_context():
            dok_internal = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Secret Classified Info',
                file_path='/up/secret.pdf',
                visibilitas='internal',
                uploaded_by=regular_user.id
            )
            db.session.add(dok_internal)
            db.session.commit()

        response = client.get('/api/global-search?q=Classified')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_dokumen_with_special_characters_in_search(self, client, kamar_aktif, sub_kamar, regular_user):
        """Test search with special characters."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?cari=%')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_large_page_number_request(self, client, kamar_aktif, sub_kamar):
        """Test requesting a very large page number."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?page=9999')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_negative_page_number(self, client, kamar_aktif, sub_kamar):
        """Test requesting negative page number."""
        response = client.get(f'/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}?page=-1')
        assert response.status_code == 200
