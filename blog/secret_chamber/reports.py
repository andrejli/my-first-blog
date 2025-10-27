"""
Secret Chamber Report Generation
Markdown report generation with analytics and decision tracking
"""
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import json
from datetime import datetime, timedelta
import statistics

from .models import SecretPoll, AnonymousVote, DecisionReport, ChamberAuditLog


class MarkdownReportGenerator:
    """Generate structured markdown reports for Secret Chamber decisions"""
    
    def __init__(self):
        self.generated_at = timezone.now()
    
    def generate_poll_report(self, poll, include_comments=True, include_statistics=True):
        """Generate comprehensive poll results report"""
        
        # Collect vote data
        votes = poll.votes.all()
        decrypted_votes = []
        
        for vote in votes:
            try:
                vote_data = vote.decrypt_vote_data()
                if vote_data:
                    decrypted_votes.append({
                        'data': vote_data,
                        'timestamp': vote.timestamp
                    })
            except:
                continue
        
        # Calculate statistics
        stats = self._calculate_poll_statistics(poll, decrypted_votes)
        
        # Generate markdown content
        markdown_content = self._render_poll_report_template(
            poll, 
            decrypted_votes, 
            stats, 
            include_comments, 
            include_statistics
        )
        
        return markdown_content
    
    def generate_periodic_summary(self, start_date, end_date):
        """Generate periodic chamber activity summary"""
        
        polls = SecretPoll.objects.filter(
            created_at__range=[start_date, end_date]
        )
        
        # Collect summary statistics
        summary_stats = {
            'total_polls': polls.count(),
            'completed_polls': polls.filter(end_date__lt=timezone.now()).count(),
            'active_polls': polls.filter(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
                is_active=True
            ).count(),
            'total_votes': sum(poll.total_votes for poll in polls),
            'avg_participation': sum(poll.participation_rate for poll in polls) / polls.count() if polls.count() > 0 else 0,
        }
        
        # Generate report
        markdown_content = self._render_periodic_summary_template(
            start_date, 
            end_date, 
            polls, 
            summary_stats
        )
        
        return markdown_content
    
    def generate_decision_analysis(self, poll):
        """Generate detailed decision analysis report"""
        
        votes = poll.votes.all()
        decrypted_votes = []
        
        for vote in votes:
            try:
                vote_data = vote.decrypt_vote_data()
                if vote_data:
                    decrypted_votes.append({
                        'data': vote_data,
                        'timestamp': vote.timestamp
                    })
            except:
                continue
        
        # Perform deep analysis
        analysis = self._perform_decision_analysis(poll, decrypted_votes)
        
        # Generate markdown
        markdown_content = self._render_decision_analysis_template(poll, analysis)
        
        return markdown_content
    
    def _calculate_poll_statistics(self, poll, decrypted_votes):
        """Calculate comprehensive poll statistics"""
        
        stats = {
            'total_votes': len(decrypted_votes),
            'participation_rate': poll.participation_rate,
            'voting_timeline': [],
            'consensus_level': 0,
            'decision_confidence': 'Unknown'
        }
        
        if not decrypted_votes:
            return stats
        
        # Timeline analysis
        vote_times = [vote['timestamp'] for vote in decrypted_votes]
        stats['voting_timeline'] = {
            'first_vote': min(vote_times),
            'last_vote': max(vote_times),
            'voting_duration': max(vote_times) - min(vote_times),
            'votes_by_day': self._group_votes_by_day(vote_times)
        }
        
        # Poll-specific analysis
        if poll.poll_type == 'multiple_choice':
            stats.update(self._analyze_multiple_choice(decrypted_votes, poll))
        elif poll.poll_type == 'rating':
            stats.update(self._analyze_rating(decrypted_votes))
        elif poll.poll_type == 'approval':
            stats.update(self._analyze_approval(decrypted_votes))
        elif poll.poll_type == 'ranking':
            stats.update(self._analyze_ranking(decrypted_votes, poll))
        
        return stats
    
    def _analyze_multiple_choice(self, votes, poll):
        """Analyze multiple choice poll results"""
        
        option_counts = {}
        total_votes = len(votes)
        
        for vote in votes:
            option_id = vote['data'].get('option_id')
            if option_id:
                option_counts[option_id] = option_counts.get(option_id, 0) + 1
        
        # Calculate percentages and determine winner
        option_percentages = {}
        winner_option = None
        max_votes = 0
        
        for option_id, count in option_counts.items():
            percentage = (count / total_votes) * 100
            option_percentages[option_id] = {
                'count': count,
                'percentage': percentage
            }
            
            if count > max_votes:
                max_votes = count
                winner_option = option_id
        
        # Calculate consensus level
        consensus_level = (max_votes / total_votes) * 100 if total_votes > 0 else 0
        
        return {
            'option_results': option_percentages,
            'winner_option': winner_option,
            'consensus_level': consensus_level,
            'decision_confidence': self._calculate_confidence_level(consensus_level)
        }
    
    def _analyze_rating(self, votes):
        """Analyze rating poll results"""
        
        ratings = [vote['data'].get('rating', 0) for vote in votes if vote['data'].get('rating')]
        
        if not ratings:
            return {}
        
        return {
            'average_rating': statistics.mean(ratings),
            'median_rating': statistics.median(ratings),
            'rating_std_dev': statistics.stdev(ratings) if len(ratings) > 1 else 0,
            'min_rating': min(ratings),
            'max_rating': max(ratings),
            'rating_distribution': {i: ratings.count(i) for i in range(1, 11)},
            'consensus_level': self._calculate_rating_consensus(ratings),
        }
    
    def _analyze_approval(self, votes):
        """Analyze approval poll results"""
        
        choices = [vote['data'].get('choice') for vote in votes if vote['data'].get('choice')]
        
        if not choices:
            return {}
        
        counts = {
            'approve': choices.count('approve'),
            'reject': choices.count('reject'),
            'abstain': choices.count('abstain')
        }
        
        total = len(choices)
        percentages = {choice: (count / total) * 100 for choice, count in counts.items()}
        
        # Determine result
        if percentages['approve'] > 50:
            result = 'APPROVED'
        elif percentages['reject'] > 50:
            result = 'REJECTED'
        else:
            result = 'NO CONSENSUS'
        
        return {
            'vote_counts': counts,
            'vote_percentages': percentages,
            'decision_result': result,
            'consensus_level': max(percentages.values()),
        }
    
    def _analyze_ranking(self, votes, poll):
        """Analyze ranking poll results"""
        
        options = list(poll.options.all())
        option_scores = {option.id: 0 for option in options}
        
        for vote in votes:
            rankings = vote['data'].get('rankings', [])
            for ranking in rankings:
                option_id = ranking.get('option_id')
                rank = ranking.get('rank')
                if option_id and rank:
                    # Lower rank = higher score (1st place gets most points)
                    score = len(options) - rank + 1
                    option_scores[option_id] += score
        
        # Sort by score
        sorted_results = sorted(
            option_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'ranking_results': sorted_results,
            'winner_option': sorted_results[0][0] if sorted_results else None,
        }
    
    def _calculate_confidence_level(self, consensus_level):
        """Calculate decision confidence level"""
        if consensus_level >= 80:
            return 'High'
        elif consensus_level >= 60:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_rating_consensus(self, ratings):
        """Calculate consensus level for rating polls"""
        if len(ratings) < 2:
            return 100
        
        std_dev = statistics.stdev(ratings)
        # Lower standard deviation = higher consensus
        consensus = max(0, 100 - (std_dev * 20))
        return consensus
    
    def _group_votes_by_day(self, vote_times):
        """Group votes by day for timeline analysis"""
        votes_by_day = {}
        
        for vote_time in vote_times:
            day = vote_time.date()
            votes_by_day[day] = votes_by_day.get(day, 0) + 1
        
        return votes_by_day
    
    def _perform_decision_analysis(self, poll, votes):
        """Perform comprehensive decision analysis"""
        
        analysis = {
            'decision_quality': 'Unknown',
            'participation_analysis': {},
            'timing_analysis': {},
            'recommendation': 'None',
            'implementation_notes': [],
            'risk_assessment': 'Low'
        }
        
        # Participation analysis
        participation_rate = poll.participation_rate
        eligible_voters = poll.eligible_voters.count()
        
        analysis['participation_analysis'] = {
            'rate': participation_rate,
            'absolute_count': len(votes),
            'eligible_voters': eligible_voters,
            'quality': 'High' if participation_rate >= 80 else 'Medium' if participation_rate >= 60 else 'Low'
        }
        
        # Timing analysis
        if votes:
            vote_times = [vote['timestamp'] for vote in votes]
            voting_duration = max(vote_times) - min(vote_times)
            
            analysis['timing_analysis'] = {
                'duration': voting_duration,
                'quick_decision': voting_duration.total_seconds() < 3600,  # Less than 1 hour
                'deliberate_decision': voting_duration.days >= 1,  # More than 1 day
            }
        
        # Generate recommendations
        recommendations = []
        
        if participation_rate < 70:
            recommendations.append("Consider extending voting period for better participation")
        
        if poll.poll_type == 'approval' and analysis.get('consensus_level', 0) < 60:
            recommendations.append("Low consensus - consider further discussion before implementation")
        
        if len(votes) >= eligible_voters:
            recommendations.append("Full participation achieved - proceed with confidence")
        
        analysis['implementation_notes'] = recommendations
        
        return analysis
    
    def _render_poll_report_template(self, poll, votes, stats, include_comments, include_statistics):
        """Render poll report using markdown template"""
        
        # Extract comments if requested
        comments = []
        if include_comments:
            for vote in votes:
                comment = vote['data'].get('comment')
                if comment:
                    comments.append({
                        'text': comment,
                        'timestamp': vote['timestamp']
                    })
        
        # Generate markdown
        markdown = f"""# Secret Chamber Decision Report - {poll.title}

**Poll Type**: {poll.get_poll_type_display()}  
**Created**: {poll.created_at.strftime('%Y-%m-%d %H:%M')}  
**Voting Period**: {poll.start_date.strftime('%Y-%m-%d %H:%M')} to {poll.end_date.strftime('%Y-%m-%d %H:%M')}  
**Participants**: {stats['total_votes']}/{poll.eligible_voters.count()} admins ({stats['participation_rate']:.1f}% participation)  
**Status**: {'Completed' if poll.is_completed else 'Active'}  
**Anonymity Level**: {poll.get_anonymity_level_display()}

## 📊 Results Summary

"""
        
        # Add poll-specific results
        if poll.poll_type == 'multiple_choice' and 'option_results' in stats:
            markdown += "### Voting Results\n\n"
            for option in poll.options.all():
                result = stats['option_results'].get(option.id, {'count': 0, 'percentage': 0})
                markdown += f"- **{option.option_text}**: {result['percentage']:.1f}% ({result['count']} votes)\n"
            
            markdown += f"\n**Consensus Level**: {stats.get('consensus_level', 0):.1f}%\n"
            markdown += f"**Decision Confidence**: {stats.get('decision_confidence', 'Unknown')}\n\n"
        
        elif poll.poll_type == 'rating' and 'average_rating' in stats:
            markdown += f"### Rating Results\n\n"
            markdown += f"- **Average Rating**: {stats['average_rating']:.2f}/10\n"
            markdown += f"- **Median Rating**: {stats['median_rating']}/10\n"
            markdown += f"- **Rating Range**: {stats['min_rating']} - {stats['max_rating']}\n"
            markdown += f"- **Consensus Level**: {stats.get('consensus_level', 0):.1f}%\n\n"
        
        elif poll.poll_type == 'approval' and 'vote_counts' in stats:
            markdown += f"### Approval Results\n\n"
            for choice, count in stats['vote_counts'].items():
                percentage = stats['vote_percentages'][choice]
                markdown += f"- **{choice.title()}**: {percentage:.1f}% ({count} votes)\n"
            
            markdown += f"\n**Decision Result**: {stats.get('decision_result', 'Unknown')}\n\n"
        
        # Add statistics section
        if include_statistics and 'voting_timeline' in stats:
            timeline = stats['voting_timeline']
            markdown += f"## 📈 Statistical Analysis\n\n"
            markdown += f"- **First Vote**: {timeline['first_vote'].strftime('%Y-%m-%d %H:%M')}\n"
            markdown += f"- **Last Vote**: {timeline['last_vote'].strftime('%Y-%m-%d %H:%M')}\n"
            markdown += f"- **Voting Duration**: {timeline['voting_duration']}\n"
            markdown += f"- **Participation Rate**: {stats['participation_rate']:.1f}% of eligible admins\n\n"
        
        # Add comments section
        if include_comments and comments:
            markdown += f"## 💭 Anonymous Comments\n\n"
            for comment in comments:
                markdown += f"> \"{comment['text']}\"\n>\n> *Submitted: {comment['timestamp'].strftime('%Y-%m-%d %H:%M')}*\n\n"
        
        # Add footer
        markdown += f"""---

**Report Generated**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Confidentiality Level**: Admin Only - Do Not Distribute  
**Report Type**: Poll Results Analysis

*This report was automatically generated by the Secret Chamber system.*
"""
        
        return markdown
    
    def _render_periodic_summary_template(self, start_date, end_date, polls, stats):
        """Render periodic summary report"""
        
        period_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        
        markdown = f"""# Secret Chamber Activity Summary

**Period**: {period_str}  
**Generated**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Summary Statistics

- **Total Polls Created**: {stats['total_polls']}
- **Completed Polls**: {stats['completed_polls']}
- **Active Polls**: {stats['active_polls']}
- **Total Votes Cast**: {stats['total_votes']}
- **Average Participation**: {stats['avg_participation']:.1f}%

## 🗳️ Poll Details

"""
        
        for poll in polls:
            status = "✅ Completed" if poll.is_completed else "🗳️ Active" if poll.is_voting_open else "⏳ Scheduled"
            markdown += f"### {poll.title}\n\n"
            markdown += f"- **Type**: {poll.get_poll_type_display()}\n"
            markdown += f"- **Status**: {status}\n"
            markdown += f"- **Participation**: {poll.participation_rate:.1f}% ({poll.total_votes} votes)\n"
            markdown += f"- **Created**: {poll.created_at.strftime('%Y-%m-%d')}\n\n"
        
        markdown += f"""---

**Report Type**: Periodic Activity Summary  
**Confidentiality Level**: Admin Only

*This report provides an overview of Secret Chamber activity for governance tracking.*
"""
        
        return markdown
    
    def _render_decision_analysis_template(self, poll, analysis):
        """Render decision analysis report"""
        
        markdown = f"""# Decision Analysis Report - {poll.title}

**Analysis Date**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Poll Created**: {poll.created_at.strftime('%Y-%m-%d %H:%M')}

## 🎯 Decision Quality Assessment

**Overall Quality**: {analysis['decision_quality']}

### Participation Analysis
- **Participation Rate**: {analysis['participation_analysis']['rate']:.1f}%
- **Vote Count**: {analysis['participation_analysis']['absolute_count']}/{analysis['participation_analysis']['eligible_voters']}
- **Participation Quality**: {analysis['participation_analysis']['quality']}

### Timing Analysis
- **Decision Speed**: {'Quick' if analysis['timing_analysis'].get('quick_decision') else 'Deliberate' if analysis['timing_analysis'].get('deliberate_decision') else 'Normal'}
- **Voting Duration**: {analysis['timing_analysis'].get('duration', 'Unknown')}

## 🎯 Recommendations

"""
        
        for note in analysis['implementation_notes']:
            markdown += f"- {note}\n"
        
        markdown += f"""

## 🛡️ Risk Assessment

**Risk Level**: {analysis['risk_assessment']}

---

**Report Type**: Decision Analysis  
**Confidentiality Level**: Admin Only

*This analysis helps evaluate the quality and implementation readiness of chamber decisions.*
"""
        
        return markdown


# Convenience functions for creating reports
def create_poll_report(poll, generated_by, include_comments=True, include_statistics=True):
    """Create and save a poll report"""
    
    generator = MarkdownReportGenerator()
    report_content = generator.generate_poll_report(
        poll, include_comments, include_statistics
    )
    
    report = DecisionReport.objects.create(
        poll=poll,
        report_type='poll_results',
        title=f"Results: {poll.title}",
        report_content=report_content,
        generated_by=generated_by,
        is_confidential=True
    )
    
    return report


def create_periodic_summary(start_date, end_date, generated_by):
    """Create and save a periodic summary report"""
    
    generator = MarkdownReportGenerator()
    report_content = generator.generate_periodic_summary(start_date, end_date)
    
    period_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    report = DecisionReport.objects.create(
        report_type='periodic_summary',
        title=f"Chamber Activity Summary: {period_str}",
        report_content=report_content,
        generated_by=generated_by,
        is_confidential=True
    )
    
    return report


def create_decision_analysis(poll, generated_by):
    """Create and save a decision analysis report"""
    
    generator = MarkdownReportGenerator()
    report_content = generator.generate_decision_analysis(poll)
    
    report = DecisionReport.objects.create(
        poll=poll,
        report_type='decision_analysis',
        title=f"Analysis: {poll.title}",
        report_content=report_content,
        generated_by=generated_by,
        is_confidential=True
    )
    
    return report