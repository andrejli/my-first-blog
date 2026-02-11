"""
Quiz Management and Taking Views
---------------------------------
Instructor quiz creation/management, student quiz taking, and grading.
"""

import random
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from blog.models import Course, Enrollment
from blog.views.helpers import instructor_required


# ================================
# INSTRUCTOR QUIZ MANAGEMENT
# ================================

@instructor_required
def course_quizzes(request, course_id):
    """View all quizzes for a course"""
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    quizzes = course.quizzes.all().order_by('-created_date')
    
    context = {
        'course': course,
        'quizzes': quizzes,
    }
    
    return render(request, 'blog/course_quizzes.html', context)


@instructor_required
def create_quiz(request, course_id):
    """Create a new quiz"""
    from blog.models import Quiz
    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        quiz_type = request.POST.get('quiz_type', 'practice')
        time_limit = request.POST.get('time_limit')
        max_attempts = request.POST.get('max_attempts', 1)
        points = request.POST.get('points', 0)
        passing_score = request.POST.get('passing_score')
        
        # Boolean fields
        shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        show_correct_answers = request.POST.get('show_correct_answers') == 'on'
        immediate_feedback = request.POST.get('immediate_feedback') == 'on'
        is_published = request.POST.get('is_published') == 'on'
        
        errors = []
        
        # Validation
        if not title:
            errors.append('Quiz title is required.')
        
        if Quiz.objects.filter(course=course, title=title).exists():
            errors.append('A quiz with this title already exists in this course.')
        
        try:
            max_attempts = int(max_attempts) if max_attempts else 1
            if max_attempts < 1:
                errors.append('Maximum attempts must be at least 1.')
        except ValueError:
            errors.append('Invalid maximum attempts value.')
        
        try:
            points = float(points) if points else 0
            if points < 0:
                errors.append('Points cannot be negative.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if time_limit:
            try:
                time_limit = int(time_limit)
                if time_limit < 1:
                    errors.append('Time limit must be at least 1 minute.')
            except ValueError:
                errors.append('Invalid time limit value.')
        else:
            time_limit = None
        
        if passing_score:
            try:
                passing_score = float(passing_score)
                if passing_score < 0 or passing_score > 100:
                    errors.append('Passing score must be between 0 and 100.')
            except ValueError:
                errors.append('Invalid passing score value.')
        else:
            passing_score = None
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create quiz
            quiz = Quiz.objects.create(
                course=course,
                title=title,
                description=description,
                quiz_type=quiz_type,
                time_limit=time_limit,
                max_attempts=max_attempts,
                points=points,
                passing_score=passing_score,
                shuffle_questions=shuffle_questions,
                show_correct_answers=show_correct_answers,
                immediate_feedback=immediate_feedback,
                is_published=is_published,
            )
            
            messages.success(request, f'Quiz "{title}" created successfully!')
            return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'course': course,
    }
    
    return render(request, 'blog/create_quiz.html', context)


@instructor_required  
def quiz_detail(request, quiz_id):
    """View quiz details and manage questions"""
    from blog.models import Quiz
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    questions = quiz.questions.all().order_by('order', 'id')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'course': quiz.course,
    }
    
    return render(request, 'blog/quiz_detail.html', context)


@instructor_required
def edit_quiz(request, quiz_id):
    """Edit quiz settings"""
    from blog.models import Quiz
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        quiz_type = request.POST.get('quiz_type', 'practice')
        time_limit = request.POST.get('time_limit')
        max_attempts = request.POST.get('max_attempts', 1)
        points = request.POST.get('points', 0)
        passing_score = request.POST.get('passing_score')
        
        # Boolean fields
        shuffle_questions = request.POST.get('shuffle_questions') == 'on'
        show_correct_answers = request.POST.get('show_correct_answers') == 'on'
        immediate_feedback = request.POST.get('immediate_feedback') == 'on'
        is_published = request.POST.get('is_published') == 'on'
        
        errors = []
        
        # Validation
        if not title:
            errors.append('Quiz title is required.')
        
        if Quiz.objects.filter(course=quiz.course, title=title).exclude(id=quiz.id).exists():
            errors.append('A quiz with this title already exists in this course.')
        
        try:
            max_attempts = int(max_attempts) if max_attempts else 1
            if max_attempts < 1:
                errors.append('Maximum attempts must be at least 1.')
        except ValueError:
            errors.append('Invalid maximum attempts value.')
        
        try:
            points = float(points) if points else 0
            if points < 0:
                errors.append('Points cannot be negative.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if time_limit:
            try:
                time_limit = int(time_limit)
                if time_limit < 1:
                    errors.append('Time limit must be at least 1 minute.')
            except ValueError:
                errors.append('Invalid time limit value.')
        else:
            time_limit = None
        
        if passing_score:
            try:
                passing_score = float(passing_score)
                if passing_score < 0 or passing_score > 100:
                    errors.append('Passing score must be between 0 and 100.')
            except ValueError:
                errors.append('Invalid passing score value.')
        else:
            passing_score = None
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update quiz
            quiz.title = title
            quiz.description = description
            quiz.quiz_type = quiz_type
            quiz.time_limit = time_limit
            quiz.max_attempts = max_attempts
            quiz.points = points
            quiz.passing_score = passing_score
            quiz.shuffle_questions = shuffle_questions
            quiz.show_correct_answers = show_correct_answers
            quiz.immediate_feedback = immediate_feedback
            quiz.is_published = is_published
            quiz.save()
            
            messages.success(request, f'Quiz "{title}" updated successfully!')
            return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'course': quiz.course,
    }
    
    return render(request, 'blog/edit_quiz.html', context)


@instructor_required
def toggle_quiz_publish(request, quiz_id):
    """Toggle quiz published status"""
    from blog.models import Quiz
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        quiz.is_published = not quiz.is_published
        quiz.save()
        
        status = "published" if quiz.is_published else "unpublished"
        messages.success(request, f'Quiz "{quiz.title}" has been {status}.')
        
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    return redirect('quiz_detail', quiz_id=quiz.id)


# ================================
# QUESTION MANAGEMENT
# ================================

@instructor_required
def add_question(request, quiz_id):
    """Add a new question to a quiz"""
    from blog.models import Quiz, Question, Answer
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        # Get form data
        question_text = request.POST.get('question_text', '').strip()
        question_type = request.POST.get('question_type', 'multiple_choice')
        points = request.POST.get('points', 1)
        explanation = request.POST.get('explanation', '').strip()
        
        errors = []
        
        # Validation
        if not question_text:
            errors.append('Question text is required.')
        
        try:
            points = float(points) if points else 1
            if points <= 0:
                errors.append('Points must be greater than 0.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create question
            question = Question.objects.create(
                quiz=quiz,
                question_text=question_text,
                question_type=question_type,
                points=points,
                explanation=explanation,
                order=quiz.questions.count() + 1
            )
            
            # Create answer choices for multiple choice and true/false questions
            if question_type == 'multiple_choice':
                # Get answer choices from form
                answer_texts = []
                correct_answers = []
                
                for i in range(1, 6):  # Support up to 5 answer choices
                    answer_text = request.POST.get(f'answer_{i}', '').strip()
                    if answer_text:
                        answer_texts.append(answer_text)
                        if request.POST.get(f'correct_{i}') == 'on':
                            correct_answers.append(len(answer_texts) - 1)
                
                if len(answer_texts) < 2:
                    messages.error(request, 'Multiple choice questions must have at least 2 answer choices.')
                    question.delete()
                elif len(correct_answers) == 0:
                    messages.error(request, 'Please select at least one correct answer.')
                    question.delete()
                else:
                    # Create answer objects
                    for i, answer_text in enumerate(answer_texts):
                        Answer.objects.create(
                            question=question,
                            answer_text=answer_text,
                            is_correct=(i in correct_answers),
                            order=i + 1
                        )
                    messages.success(request, f'Question added successfully!')
                    return redirect('quiz_detail', quiz_id=quiz.id)
            
            elif question_type == 'true_false':
                # Create True/False answers
                correct_answer = request.POST.get('tf_correct', 'true')
                Answer.objects.create(
                    question=question,
                    answer_text='True',
                    is_correct=(correct_answer == 'true'),
                    order=1
                )
                Answer.objects.create(
                    question=question,
                    answer_text='False',
                    is_correct=(correct_answer == 'false'),
                    order=2
                )
                messages.success(request, f'Question added successfully!')
                return redirect('quiz_detail', quiz_id=quiz.id)
            
            else:  # short_answer
                messages.success(request, f'Question added successfully!')
                return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'course': quiz.course,
    }
    
    return render(request, 'blog/add_question.html', context)


@instructor_required
def edit_question(request, question_id):
    """Edit an existing question"""
    from blog.models import Question, Answer
    question = get_object_or_404(Question, id=question_id, quiz__course__instructor=request.user)
    quiz = question.quiz
    
    if request.method == 'POST':
        # Get form data
        question_text = request.POST.get('question_text', '').strip()
        question_type = request.POST.get('question_type', question.question_type)
        points = request.POST.get('points', question.points)
        explanation = request.POST.get('explanation', '').strip()
        
        errors = []
        
        # Validation
        if not question_text:
            errors.append('Question text is required.')
        
        try:
            points = float(points) if points else 1
            if points <= 0:
                errors.append('Points must be greater than 0.')
        except ValueError:
            errors.append('Invalid points value.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update question
            question.question_text = question_text
            question.question_type = question_type
            question.points = points
            question.explanation = explanation
            question.save()
            
            # Handle answer choices
            if question_type in ['multiple_choice', 'true_false']:
                # Delete existing answers
                question.answers.all().delete()
                
                if question_type == 'multiple_choice':
                    # Get answer choices from form
                    answer_texts = []
                    correct_answers = []
                    
                    for i in range(1, 6):  # Support up to 5 answer choices
                        answer_text = request.POST.get(f'answer_{i}', '').strip()
                        if answer_text:
                            answer_texts.append(answer_text)
                            if request.POST.get(f'correct_{i}') == 'on':
                                correct_answers.append(len(answer_texts) - 1)
                    
                    if len(answer_texts) < 2:
                        messages.error(request, 'Multiple choice questions must have at least 2 answer choices.')
                    elif len(correct_answers) == 0:
                        messages.error(request, 'Please select at least one correct answer.')
                    else:
                        # Create answer objects
                        for i, answer_text in enumerate(answer_texts):
                            Answer.objects.create(
                                question=question,
                                answer_text=answer_text,
                                is_correct=(i in correct_answers),
                                order=i + 1
                            )
                        messages.success(request, f'Question updated successfully!')
                        return redirect('quiz_detail', quiz_id=quiz.id)
                
                elif question_type == 'true_false':
                    # Create True/False answers
                    correct_answer = request.POST.get('tf_correct', 'true')
                    Answer.objects.create(
                        question=question,
                        answer_text='True',
                        is_correct=(correct_answer == 'true'),
                        order=1
                    )
                    Answer.objects.create(
                        question=question,
                        answer_text='False',
                        is_correct=(correct_answer == 'false'),
                        order=2
                    )
                    messages.success(request, f'Question updated successfully!')
                    return redirect('quiz_detail', quiz_id=quiz.id)
            else:
                messages.success(request, f'Question updated successfully!')
                return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'question': question,
        'quiz': quiz,
        'course': quiz.course,
        'answers': question.answers.all().order_by('order'),
    }
    
    return render(request, 'blog/edit_question.html', context)


@instructor_required
def delete_question(request, question_id):
    """Delete a question from a quiz"""
    from blog.models import Question
    question = get_object_or_404(Question, id=question_id, quiz__course__instructor=request.user)
    quiz = question.quiz
    
    if request.method == 'POST':
        question_text = question.question_text[:50] + "..." if len(question.question_text) > 50 else question.question_text
        question.delete()
        messages.success(request, f'Question "{question_text}" deleted successfully!')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    context = {
        'question': question,
        'quiz': quiz,
        'course': quiz.course,
    }
    
    return render(request, 'blog/delete_question.html', context)


@instructor_required
def reorder_questions(request, quiz_id):
    """Reorder questions in a quiz"""
    from blog.models import Quiz, Question
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    if request.method == 'POST':
        question_ids = request.POST.getlist('question_order')
        
        for i, question_id in enumerate(question_ids):
            try:
                question = Question.objects.get(id=question_id, quiz=quiz)
                question.order = i + 1
                question.save()
            except Question.DoesNotExist:
                continue
        
        messages.success(request, 'Questions reordered successfully!')
        return redirect('quiz_detail', quiz_id=quiz.id)
    
    questions = quiz.questions.all().order_by('order', 'id')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'course': quiz.course,
    }
    
    return render(request, 'blog/reorder_questions.html', context)


# ================================
# STUDENT QUIZ TAKING
# ================================

def quiz_list_for_students(request, course_id):
    """List all available quizzes for students in a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if student is enrolled in the course
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'student':
        messages.error(request, 'Only students can take quizzes.')
        return redirect('course_list')
    
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, 'You must be enrolled in this course to view quizzes.')
        return redirect('course_detail', course_id=course_id)
    
    # Get published quizzes that are available
    from blog.models import Quiz, QuizAttempt
    quizzes = Quiz.objects.filter(
        course=course, 
        is_published=True
    ).select_related('course').prefetch_related('attempts').order_by('-created_date')
    
    # Add attempt information for each quiz (cache count to avoid duplicate queries)
    quiz_data = []
    for quiz in quizzes:
        user_attempts = quiz.attempts.filter(student=request.user).order_by('-started_at')
        user_attempts_count = user_attempts.count()  # Cache the count
        
        quiz_info = {
            'quiz': quiz,
            'total_attempts': user_attempts_count,
            'max_attempts': quiz.max_attempts,
            'can_attempt': user_attempts_count < quiz.max_attempts if quiz.max_attempts else True,
            'best_score': None,
            'last_attempt': user_attempts.first() if user_attempts_count > 0 else None,
            'is_available': quiz.is_available,
        }
        
        # Calculate best score
        completed_attempts = user_attempts.filter(status='completed')
        if completed_attempts.exists():
            quiz_info['best_score'] = max(attempt.percentage or 0 for attempt in completed_attempts)
        
        quiz_data.append(quiz_info)
    
    context = {
        'course': course,
        'quiz_data': quiz_data,
        'quizzes': quizzes,  # For backward compatibility with tests
    }
    
    return render(request, 'blog/student_quiz_list.html', context)


def start_quiz(request, quiz_id):
    """Start a new quiz attempt"""
    from blog.models import Quiz, QuizAttempt
    quiz = get_object_or_404(Quiz, id=quiz_id, is_published=True)
    
    # Check if student is enrolled
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'student':
        messages.error(request, 'Only students can take quizzes.')
        return redirect('course_list')
    
    if not Enrollment.objects.filter(student=request.user, course=quiz.course).exists():
        messages.error(request, 'You must be enrolled in this course to take quizzes.')
        return redirect('course_detail', course_id=quiz.course.id)
    
    # Check quiz availability
    if not quiz.is_available:
        messages.error(request, 'This quiz is not currently available.')
        return redirect('student_quiz_list', course_id=quiz.course.id)
    
    # Check if quiz has questions
    if quiz.total_questions == 0:
        messages.error(request, 'This quiz has no questions and cannot be taken.')
        return redirect('student_quiz_list', course_id=quiz.course.id)
    
    # Check attempt limits
    existing_attempts = QuizAttempt.objects.filter(student=request.user, quiz=quiz)
    if quiz.max_attempts and existing_attempts.count() >= quiz.max_attempts:
        messages.error(request, f'You have reached the maximum number of attempts ({quiz.max_attempts}) for this quiz.')
        return redirect('student_quiz_list', course_id=quiz.course.id)
    
    # Check for existing in-progress attempt
    in_progress_attempt = existing_attempts.filter(status='in_progress').first()
    if in_progress_attempt:
        return redirect('take_quiz', attempt_id=in_progress_attempt.id)
    
    # Create new attempt
    attempt_number = existing_attempts.count() + 1
    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        attempt_number=attempt_number
    )
    
    messages.success(request, f'Quiz attempt started! You have {attempt_number} of {quiz.max_attempts or "unlimited"} attempts.')
    return redirect('take_quiz', attempt_id=attempt.id)


def take_quiz(request, attempt_id):
    """Take a quiz - show questions and collect answers"""
    from blog.models import QuizAttempt, QuizResponse, Question, Answer
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.status != 'in_progress':
        messages.error(request, 'This quiz attempt is no longer active.')
        return redirect('quiz_results', attempt_id=attempt.id)
    
    quiz = attempt.quiz
    questions = quiz.questions.all().order_by('order', 'id')
    
    # Shuffle questions if enabled
    if quiz.shuffle_questions:
        questions = list(questions)
        random.shuffle(questions)
    
    if request.method == 'POST':
        # Process quiz submission
        for question in questions:
            response, created = QuizResponse.objects.get_or_create(
                attempt=attempt,
                question=question,
                defaults={'answered_at': timezone.now()}
            )
            
            if question.question_type == 'multiple_choice':
                answer_id = request.POST.get(f'question_{question.id}')
                if answer_id:
                    try:
                        selected_answer = Answer.objects.get(id=answer_id, question=question)
                        response.selected_answer = selected_answer
                        response.text_answer = ''
                    except Answer.DoesNotExist:
                        pass
            
            elif question.question_type == 'true_false':
                answer_value = request.POST.get(f'question_{question.id}')
                if answer_value:
                    # Check if it's an answer ID (from answer selection) or text value
                    try:
                        # Try as answer ID first
                        answer_id = int(answer_value)
                        selected_answer = Answer.objects.get(id=answer_id, question=question)
                        response.selected_answer = selected_answer
                        response.text_answer = selected_answer.answer_text
                    except (ValueError, Answer.DoesNotExist):
                        # Fall back to text value handling
                        if answer_value in ['True', 'False']:
                            response.text_answer = answer_value
                            response.selected_answer = None
                            # Try to find matching answer for auto-grading
                            try:
                                matching_answer = Answer.objects.get(
                                    question=question, 
                                    answer_text__iexact=answer_value
                                )
                                response.selected_answer = matching_answer
                            except Answer.DoesNotExist:
                                pass
            
            elif question.question_type == 'short_answer':
                text_answer = request.POST.get(f'question_{question.id}', '').strip()
                response.text_answer = text_answer
                response.selected_answer = None
            
            response.answered_at = timezone.now()
            response.save()
            
            # Auto-grade MC and T/F questions
            if question.question_type in ['multiple_choice', 'true_false']:
                response.auto_grade()
        
        # Complete the attempt
        attempt.complete_attempt()
        messages.success(request, 'Quiz submitted successfully!')
        return redirect('quiz_results', attempt_id=attempt.id)
    
    # Get existing responses
    responses = {r.question_id: r for r in QuizResponse.objects.filter(attempt=attempt)}
    
    # Add response data to questions
    for question in questions:
        question.current_response = responses.get(question.id)
        # For now, we'll use the original order of answers
        # Answer shuffling can be added as a future feature
        question.shuffled_answers = question.answers.all().order_by('order')
    
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'questions': questions,
        'responses': responses,
    }
    
    return render(request, 'blog/take_quiz.html', context)


def quiz_results(request, attempt_id):
    """Show quiz results to student"""
    from blog.models import QuizAttempt
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    
    if attempt.status == 'in_progress':
        messages.warning(request, 'Quiz is still in progress.')
        return redirect('take_quiz', attempt_id=attempt.id)
    
    quiz = attempt.quiz
    responses = attempt.responses.all().select_related('question', 'selected_answer')
    
    # Calculate statistics
    total_questions = responses.count()
    correct_answers = responses.filter(is_correct=True).count()
    
    context = {
        'attempt': attempt,
        'quiz': quiz,
        'responses': responses,
        'total_questions': total_questions,
        'correct_answers': correct_answers,
        'show_correct_answers': quiz.show_correct_answers,
    }
    
    return render(request, 'blog/quiz_results.html', context)


# ================================
# INSTRUCTOR QUIZ GRADING
# ================================

@instructor_required
def quiz_attempts(request, quiz_id):
    """View all attempts for a quiz (instructor)"""
    from blog.models import Quiz, QuizAttempt
    quiz = get_object_or_404(Quiz, id=quiz_id, course__instructor=request.user)
    
    attempts = QuizAttempt.objects.filter(quiz=quiz).select_related(
        'student', 'student__userprofile'
    ).order_by('-started_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        attempts = attempts.filter(status=status_filter)
    
    # Statistics
    total_attempts = attempts.count()
    completed_attempts = attempts.filter(status='completed')
    average_score = None
    if completed_attempts.exists():
        scores = [attempt.percentage for attempt in completed_attempts if attempt.percentage is not None]
        if scores:
            average_score = sum(scores) / len(scores)
    
    context = {
        'quiz': quiz,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'completed_attempts': completed_attempts.count(),
        'average_score': average_score,
        'status_filter': status_filter,
    }
    
    return render(request, 'blog/quiz_attempts.html', context)


@instructor_required
def grade_quiz_attempt(request, attempt_id):
    """Grade a specific quiz attempt (instructor)"""
    from blog.models import QuizAttempt, QuizResponse
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz__course__instructor=request.user)
    
    responses = QuizResponse.objects.filter(attempt=attempt).select_related(
        'question', 'selected_answer'
    ).order_by('question__order', 'question__id')
    
    if request.method == 'POST':
        # Process grading for short answer questions
        for response in responses:
            if response.question.question_type == 'short_answer':
                points_key = f'points_{response.id}'
                feedback_key = f'feedback_{response.id}'
                
                points = request.POST.get(points_key, '0')
                feedback = request.POST.get(feedback_key, '').strip()
                
                try:
                    points = float(points)
                    points = max(0, min(points, float(response.question.points)))  # Clamp between 0 and max points
                    response.points_earned = points
                    response.is_correct = points > 0
                except ValueError:
                    response.points_earned = 0
                    response.is_correct = False
                
                response.feedback = feedback
                response.save()
        
        # Recalculate attempt score
        attempt.complete_attempt()
        messages.success(request, 'Quiz graded successfully!')
        return redirect('quiz_attempts', quiz_id=attempt.quiz.id)
    
    # Separate responses by type
    auto_graded = responses.filter(question__question_type__in=['multiple_choice', 'true_false'])
    manual_graded = responses.filter(question__question_type='short_answer')
    
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'responses': responses,
        'auto_graded': auto_graded,
        'manual_graded': manual_graded,
    }
    
    return render(request, 'blog/grade_quiz_attempt.html', context)
