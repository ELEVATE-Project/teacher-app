"""
Property-Based Tests for TopicSelectorService
==============================================

Tests using Hypothesis to validate correctness properties for topic selection.

Feature: module-lesson-builder, Property 1: Topic Hierarchy Consistency
Validates: Requirements 1.1, 1.2, 1.3, 1.4
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume
from typing import List, Set

from ..services.topic_selector import TopicSelectorService


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="module")
def topic_service():
    """Create a TopicSelectorService instance for testing."""
    return TopicSelectorService()


@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def run_async(coro):
    """Helper to run async functions in sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =============================================================================
# Database Ground Truth Helpers
# =============================================================================

def get_all_classes_from_db(service: TopicSelectorService) -> Set[str]:
    """Get all unique classes directly from database."""
    with service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT source FROM documents")
        classes = set()
        for row in cursor.fetchall():
            parts = row['source'].split('|')
            if parts:
                classes.add(parts[0])
        return classes


def get_all_subjects_for_class_from_db(service: TopicSelectorService, class_name: str) -> Set[str]:
    """Get all unique subjects for a class directly from database."""
    with service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT source FROM documents WHERE source LIKE ?",
            (f"{class_name}|%",)
        )
        subjects = set()
        for row in cursor.fetchall():
            parts = row['source'].split('|')
            if len(parts) > 1:
                subjects.add(parts[1])
        return subjects


def get_all_topics_for_subject_from_db(
    service: TopicSelectorService, 
    class_name: str, 
    subject: str
) -> Set[str]:
    """Get all unique topics (book codes) for a class+subject directly from database."""
    with service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT source FROM documents WHERE source LIKE ?",
            (f"{class_name}|{subject}|%",)
        )
        topics = set()
        for row in cursor.fetchall():
            parts = row['source'].split('|')
            if len(parts) > 2:
                topics.add(parts[2])
        return topics


def content_exists_in_db(
    service: TopicSelectorService,
    class_name: str,
    subject: str,
    topic: str
) -> bool:
    """Check if content exists in database for given combination."""
    with service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM documents WHERE source LIKE ?",
            (f"{class_name}|{subject}|{topic}|%",)
        )
        return cursor.fetchone()[0] > 0


# =============================================================================
# Property 1: Topic Hierarchy Consistency
# =============================================================================

class TestTopicHierarchyConsistency:
    """
    Feature: module-lesson-builder, Property 1: Topic Hierarchy Consistency
    
    For any class selected from the database, all returned subjects must exist 
    in the database for that class, and for any class+subject combination, 
    all returned topics must exist in the database for that combination.
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """

    def test_all_returned_classes_exist_in_database(self, topic_service):
        """
        Property 1.1: All classes returned by get_available_classes() 
        must exist in the database.
        
        **Validates: Requirements 1.1**
        """
        # Get classes from service
        service_classes = set(run_async(topic_service.get_available_classes()))
        
        # Get classes directly from database
        db_classes = get_all_classes_from_db(topic_service)
        
        # All service classes must be in database
        assert service_classes.issubset(db_classes), (
            f"Service returned classes not in database: {service_classes - db_classes}"
        )
        
        # Service should return all database classes (completeness)
        assert service_classes == db_classes, (
            f"Service missing classes from database: {db_classes - service_classes}"
        )

    @given(st.sampled_from(["Class_6", "Class_7", "Class_8"]))
    @settings(max_examples=10)
    def test_all_returned_subjects_exist_in_database_for_class(
        self, 
        topic_service, 
        class_name: str
    ):
        """
        Property 1.2: For any class, all subjects returned by 
        get_subjects_for_class() must exist in the database for that class.
        
        **Validates: Requirements 1.2**
        """
        # Get subjects from service
        service_subjects = set(run_async(topic_service.get_subjects_for_class(class_name)))
        
        # Get subjects directly from database
        db_subjects = get_all_subjects_for_class_from_db(topic_service, class_name)
        
        # All service subjects must be in database
        assert service_subjects.issubset(db_subjects), (
            f"Service returned subjects not in database for {class_name}: "
            f"{service_subjects - db_subjects}"
        )
        
        # Service should return all database subjects (completeness)
        assert service_subjects == db_subjects, (
            f"Service missing subjects from database for {class_name}: "
            f"{db_subjects - service_subjects}"
        )

    def test_all_returned_topics_exist_in_database_for_class_subject(self, topic_service):
        """
        Property 1.3: For any class+subject combination, all topics returned by
        get_topics_for_subject() must exist in the database.
        
        **Validates: Requirements 1.3**
        """
        # Get all classes
        classes = run_async(topic_service.get_available_classes())
        
        for class_name in classes:
            subjects = run_async(topic_service.get_subjects_for_class(class_name))
            
            for subject in subjects:
                # Get topics from service
                service_topics = run_async(
                    topic_service.get_topics_for_subject(class_name, subject)
                )
                service_topic_names = {t.topic_name for t in service_topics}
                
                # Get topics directly from database
                db_topics = get_all_topics_for_subject_from_db(
                    topic_service, class_name, subject
                )
                
                # All service topics must be in database
                assert service_topic_names.issubset(db_topics), (
                    f"Service returned topics not in database for "
                    f"{class_name}/{subject}: {service_topic_names - db_topics}"
                )
                
                # Service should return all database topics (completeness)
                assert service_topic_names == db_topics, (
                    f"Service missing topics from database for "
                    f"{class_name}/{subject}: {db_topics - service_topic_names}"
                )

    def test_content_retrieval_returns_only_existing_content(self, topic_service):
        """
        Property 1.4: For any topic, get_content_for_topic() must return 
        content that actually exists in the database.
        
        **Validates: Requirements 1.4**
        """
        # Get a valid class/subject/topic combination
        classes = run_async(topic_service.get_available_classes())
        if len(classes) == 0:
            pytest.skip("No classes available in database")
        
        class_name = classes[0]
        subjects = run_async(topic_service.get_subjects_for_class(class_name))
        if len(subjects) == 0:
            pytest.skip("No subjects available for class")
        
        subject = subjects[0]
        topics = run_async(topic_service.get_topics_for_subject(class_name, subject))
        if len(topics) == 0:
            pytest.skip("No topics available for subject")
        
        topic = topics[0].topic_name
        
        # Get content from service
        content_list = run_async(
            topic_service.get_content_for_topic(class_name, subject, topic)
        )
        
        # Verify each content item exists in database
        with topic_service._get_connection() as conn:
            cursor = conn.cursor()
            for content in content_list:
                cursor.execute(
                    "SELECT COUNT(*) FROM documents WHERE source = ? AND content = ?",
                    (content.source, content.content)
                )
                count = cursor.fetchone()[0]
                assert count > 0, (
                    f"Content not found in database: source={content.source}"
                )

    def test_nonexistent_class_returns_empty_subjects(self, topic_service):
        """
        Property 1.5: Querying subjects for a non-existent class 
        should return an empty list.
        
        **Validates: Requirements 1.5**
        """
        subjects = run_async(topic_service.get_subjects_for_class("NonExistent_Class_99"))
        assert subjects == [], f"Expected empty list, got {subjects}"

    def test_nonexistent_subject_returns_empty_topics(self, topic_service):
        """
        Property 1.5: Querying topics for a non-existent subject 
        should return an empty list.
        
        **Validates: Requirements 1.5**
        """
        topics = run_async(
            topic_service.get_topics_for_subject("Class_6", "NonExistent_Subject")
        )
        assert topics == [], f"Expected empty list, got {topics}"

    def test_nonexistent_topic_returns_empty_content(self, topic_service):
        """
        Property 1.5: Querying content for a non-existent topic 
        should return an empty list.
        
        **Validates: Requirements 1.5**
        """
        content = run_async(
            topic_service.get_content_for_topic("Class_6", "Science", "nonexistent_topic")
        )
        assert content == [], f"Expected empty list, got {content}"

    def test_check_content_exists_consistency(self, topic_service):
        """
        Property 1.6: check_content_exists() must be consistent with 
        get_content_for_topic() - if content exists, retrieval should return it.
        
        **Validates: Requirements 1.4, 1.5**
        """
        # Test with existing content
        classes = run_async(topic_service.get_available_classes())
        if classes:
            class_name = classes[0]
            subjects = run_async(topic_service.get_subjects_for_class(class_name))
            if subjects:
                subject = subjects[0]
                topics = run_async(
                    topic_service.get_topics_for_subject(class_name, subject)
                )
                if topics:
                    topic = topics[0].topic_name
                    
                    # Check existence
                    exists = run_async(
                        topic_service.check_content_exists(class_name, subject, topic)
                    )
                    
                    # Get content
                    content = run_async(
                        topic_service.get_content_for_topic(class_name, subject, topic)
                    )
                    
                    # Consistency check
                    assert exists == (len(content) > 0), (
                        f"Inconsistency: check_content_exists={exists}, "
                        f"content_count={len(content)}"
                    )
        
        # Test with non-existing content
        exists = run_async(
            topic_service.check_content_exists("Class_99", "FakeSubject", "fake_topic")
        )
        content = run_async(
            topic_service.get_content_for_topic("Class_99", "FakeSubject", "fake_topic")
        )
        assert exists == (len(content) > 0), (
            f"Inconsistency for non-existing: check_content_exists={exists}, "
            f"content_count={len(content)}"
        )

    @given(st.sampled_from(["Class_6", "Class_7", "Class_8"]))
    @settings(max_examples=10, deadline=None)
    def test_topic_content_count_matches_actual_content(
        self, 
        topic_service, 
        class_name: str
    ):
        """
        Property 1.7: TopicInfo.content_count must match the actual number 
        of content items retrievable for that topic.
        
        **Validates: Requirements 1.3, 1.4**
        """
        subjects = run_async(topic_service.get_subjects_for_class(class_name))
        assume(len(subjects) > 0)
        
        subject = subjects[0]
        topics = run_async(topic_service.get_topics_for_subject(class_name, subject))
        
        for topic_info in topics:
            # Get actual content
            content = run_async(
                topic_service.get_content_for_topic(
                    class_name, subject, topic_info.topic_name
                )
            )
            
            # Content count should match
            assert topic_info.content_count == len(content), (
                f"Content count mismatch for {topic_info.topic_name}: "
                f"reported={topic_info.content_count}, actual={len(content)}"
            )
