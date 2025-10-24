"""
CLI Security Management Commands for Django LMS
Advanced command-line tools for security monitoring and administration
"""

import json
import csv
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg, Max, Min
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import ipaddress
import whois

from blog.models_security import (
    SecurityEvent, SystemMetrics, ThreatIntelligence, 
    AuditLog, AlertRule
)


class Command(BaseCommand):
    """
    Security CLI Management Tool
    
    Usage:
        python manage.py security_monitor [command] [options]
    
    Commands:
        dashboard           - Display security dashboard
        events              - List and analyze security events  
        threats             - Manage threat intelligence
        metrics             - View system metrics
        audit               - Review audit logs
        alerts              - Manage alert rules
        analyze             - Advanced security analysis
        export              - Export security data
        block               - Block IP addresses
        unblock             - Unblock IP addresses
        whitelist           - Whitelist IP addresses
        investigate         - Investigate security incidents
    """
    
    help = 'Advanced CLI security monitoring and management tool'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.console = Console()
    
    def add_arguments(self, parser):
        parser.add_argument(
            'command',
            choices=[
                'dashboard', 'events', 'threats', 'metrics', 'audit', 
                'alerts', 'analyze', 'export', 'block', 'unblock', 
                'whitelist', 'investigate'
            ],
            help='Security monitoring command'
        )
        
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Time range in hours (default: 24)'
        )
        
        parser.add_argument(
            '--severity',
            choices=['low', 'medium', 'high', 'critical'],
            help='Filter by severity level'
        )
        
        parser.add_argument(
            '--event-type',
            help='Filter by event type'
        )
        
        parser.add_argument(
            '--ip',
            help='Filter by IP address'
        )
        
        parser.add_argument(
            '--user',
            help='Filter by username'
        )
        
        parser.add_argument(
            '--blocked',
            action='store_true',
            help='Show only blocked events'
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit number of results (default: 50)'
        )
        
        parser.add_argument(
            '--format',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format (default: table)'
        )
        
        parser.add_argument(
            '--output',
            help='Output file path'
        )
        
        parser.add_argument(
            '--confidence',
            type=int,
            help='Minimum confidence level for threats'
        )
        
        parser.add_argument(
            '--auto-block',
            action='store_true',
            help='Automatically block high-confidence threats'
        )
    
    def handle(self, *args, **options):
        command = options['command']
        
        try:
            method = getattr(self, f'handle_{command}')
            method(options)
        except AttributeError:
            raise CommandError(f'Unknown command: {command}')
        except Exception as e:
            self.console.print(f'[red]Error: {str(e)}[/red]')
            raise CommandError(str(e))
    
    def handle_dashboard(self, options):
        """Display comprehensive security dashboard"""
        hours = options['hours']
        since = timezone.now() - timedelta(hours=hours)
        
        # Security events summary
        events = SecurityEvent.objects.filter(timestamp__gte=since)
        total_events = events.count()
        
        severity_counts = dict(events.values('severity').annotate(count=Count('id')))
        event_type_counts = dict(events.values('event_type').annotate(count=Count('id')))
        
        blocked_events = events.filter(blocked=True).count()
        unique_ips = events.values('ip_address').distinct().count()
        
        # Threat intelligence summary
        threats = ThreatIntelligence.objects.all()
        blocked_threats = threats.filter(blocked=True).count()
        high_confidence_threats = threats.filter(confidence__gte=80).count()
        
        # System metrics summary
        metrics = SystemMetrics.objects.filter(timestamp__gte=since)
        avg_cpu = metrics.filter(metric_type='cpu_usage').aggregate(avg=Avg('value'))['avg'] or 0
        avg_memory = metrics.filter(metric_type='memory_usage').aggregate(avg=Avg('value'))['avg'] or 0
        
        # Create dashboard
        dashboard = Table(title=f"🔒 Security Dashboard - Last {hours} Hours")
        dashboard.add_column("Metric", style="cyan", no_wrap=True)
        dashboard.add_column("Value", style="magenta")
        dashboard.add_column("Status", style="green")
        
        # Security events section
        dashboard.add_row("", "", "")
        dashboard.add_row("[bold]SECURITY EVENTS[/bold]", "", "")
        dashboard.add_row("Total Events", str(total_events), self._get_status_icon(total_events, 100, 500))
        dashboard.add_row("Blocked Events", str(blocked_events), self._get_status_icon(blocked_events, 10, 50))
        dashboard.add_row("Unique IPs", str(unique_ips), self._get_status_icon(unique_ips, 20, 100))
        
        # Severity breakdown
        for severity in ['critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            dashboard.add_row(f"{severity.title()} Severity", str(count), 
                             self._get_severity_status(severity, count))
        
        # Threat intelligence section
        dashboard.add_row("", "", "")
        dashboard.add_row("[bold]THREAT INTELLIGENCE[/bold]", "", "")
        dashboard.add_row("Blocked Threats", str(blocked_threats), "🛡️")
        dashboard.add_row("High Confidence", str(high_confidence_threats), "⚠️")
        
        # System metrics section
        dashboard.add_row("", "", "")
        dashboard.add_row("[bold]SYSTEM METRICS[/bold]", "", "")
        dashboard.add_row("Avg CPU Usage", f"{avg_cpu:.1f}%", self._get_performance_status(avg_cpu))
        dashboard.add_row("Avg Memory Usage", f"{avg_memory:.1f}%", self._get_performance_status(avg_memory))
        
        self.console.print(dashboard)
        
        # Top threats
        if blocked_threats > 0:
            self._show_top_threats(limit=5)
        
        # Recent high severity events
        high_severity = events.filter(severity__in=['high', 'critical']).order_by('-timestamp')[:5]
        if high_severity.exists():
            self._show_recent_events(high_severity, "Recent High Severity Events")
    
    def handle_events(self, options):
        """List and analyze security events"""
        queryset = SecurityEvent.objects.all()
        
        # Apply filters
        queryset = self._apply_event_filters(queryset, options)
        
        # Order and limit
        queryset = queryset.order_by('-timestamp')[:options['limit']]
        
        if options['format'] == 'json':
            self._export_events_json(queryset, options.get('output'))
        elif options['format'] == 'csv':
            self._export_events_csv(queryset, options.get('output'))
        else:
            self._display_events_table(queryset)
    
    def handle_threats(self, options):
        """Manage threat intelligence"""
        queryset = ThreatIntelligence.objects.all()
        
        # Apply filters
        if options.get('confidence'):
            queryset = queryset.filter(confidence__gte=options['confidence'])
        
        if options.get('ip'):
            queryset = queryset.filter(ip_address__icontains=options['ip'])
        
        # Auto-block high confidence threats
        if options.get('auto_block'):
            high_confidence = queryset.filter(confidence__gte=90, blocked=False)
            blocked_count = high_confidence.update(blocked=True)
            self.console.print(f"[green]Auto-blocked {blocked_count} high-confidence threats[/green]")
        
        # Display threats
        queryset = queryset.order_by('-confidence')[:options['limit']]
        self._display_threats_table(queryset)
    
    def handle_metrics(self, options):
        """View system metrics"""
        hours = options['hours']
        since = timezone.now() - timedelta(hours=hours)
        
        metrics = SystemMetrics.objects.filter(timestamp__gte=since)
        
        # Group by metric type
        metric_types = metrics.values('metric_type').distinct()
        
        for metric_type in metric_types:
            type_metrics = metrics.filter(metric_type=metric_type['metric_type'])
            
            table = Table(title=f"System Metrics: {metric_type['metric_type']}")
            table.add_column("Timestamp", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_column("Unit", style="green")
            
            for metric in type_metrics.order_by('-timestamp')[:20]:
                table.add_row(
                    metric.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    str(metric.value),
                    metric.unit or ""
                )
            
            self.console.print(table)
            self.console.print()
    
    def handle_audit(self, options):
        """Review audit logs"""
        queryset = AuditLog.objects.all()
        
        # Apply filters
        if options.get('user'):
            queryset = queryset.filter(user__username__icontains=options['user'])
        
        if options.get('hours'):
            since = timezone.now() - timedelta(hours=options['hours'])
            queryset = queryset.filter(timestamp__gte=since)
        
        # Display audit logs
        queryset = queryset.order_by('-timestamp')[:options['limit']]
        self._display_audit_table(queryset)
    
    def handle_alerts(self, options):
        """Manage alert rules"""
        alerts = AlertRule.objects.all()
        
        table = Table(title="Alert Rules Configuration")
        table.add_column("Name", style="cyan")
        table.add_column("Active", style="green")
        table.add_column("Event Type", style="yellow")
        table.add_column("Condition", style="magenta")
        table.add_column("Severity", style="red")
        table.add_column("Last Triggered", style="blue")
        
        for alert in alerts:
            table.add_row(
                alert.name,
                "✅" if alert.is_active else "❌",
                alert.event_type or "All",
                f"{alert.condition_type}: {alert.threshold_value}",
                alert.alert_severity,
                alert.last_triggered.strftime("%Y-%m-%d %H:%M") if alert.last_triggered else "Never"
            )
        
        self.console.print(table)
    
    def handle_analyze(self, options):
        """Advanced security analysis"""
        hours = options['hours']
        since = timezone.now() - timedelta(hours=hours)
        
        self.console.print(Panel.fit("🔍 Advanced Security Analysis", style="bold blue"))
        
        # IP analysis
        self._analyze_ip_patterns(since, options['limit'])
        
        # Attack pattern analysis
        self._analyze_attack_patterns(since)
        
        # User behavior analysis  
        self._analyze_user_behavior(since)
        
        # Geographic analysis
        self._analyze_geographic_patterns(since)
    
    def handle_block(self, options):
        """Block IP addresses"""
        if not options.get('ip'):
            raise CommandError("IP address required. Use --ip <address>")
        
        ip = options['ip']
        
        # Validate IP
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            raise CommandError(f"Invalid IP address: {ip}")
        
        # Create or update threat intelligence
        threat, created = ThreatIntelligence.objects.get_or_create(
            ip_address=ip,
            defaults={
                'threat_type': 'malicious_ip',
                'blocked': True,
                'confidence': 100,
                'source': 'manual_cli',
                'description': 'Manually blocked via CLI'
            }
        )
        
        if not created:
            threat.blocked = True
            threat.save()
        
        self.console.print(f"[green]✅ Blocked IP address: {ip}[/green]")
    
    def handle_unblock(self, options):
        """Unblock IP addresses"""
        if not options.get('ip'):
            raise CommandError("IP address required. Use --ip <address>")
        
        ip = options['ip']
        
        try:
            threat = ThreatIntelligence.objects.get(ip_address=ip)
            threat.blocked = False
            threat.save()
            self.console.print(f"[green]✅ Unblocked IP address: {ip}[/green]")
        except ThreatIntelligence.DoesNotExist:
            self.console.print(f"[yellow]⚠️  No threat record found for: {ip}[/yellow]")
    
    def handle_whitelist(self, options):
        """Whitelist IP addresses"""
        if not options.get('ip'):
            raise CommandError("IP address required. Use --ip <address>")
        
        ip = options['ip']
        
        threat, created = ThreatIntelligence.objects.get_or_create(
            ip_address=ip,
            defaults={
                'threat_type': 'whitelisted',
                'blocked': False,
                'whitelisted': True,
                'confidence': 0,
                'source': 'manual_cli',
                'description': 'Manually whitelisted via CLI'
            }
        )
        
        if not created:
            threat.whitelisted = True
            threat.blocked = False
            threat.save()
        
        self.console.print(f"[green]✅ Whitelisted IP address: {ip}[/green]")
    
    def handle_investigate(self, options):
        """Investigate security incidents"""
        if not options.get('ip'):
            raise CommandError("IP address required for investigation. Use --ip <address>")
        
        ip = options['ip']
        self.console.print(Panel.fit(f"🔍 Security Investigation: {ip}", style="bold red"))
        
        # Security events from this IP
        events = SecurityEvent.objects.filter(ip_address=ip).order_by('-timestamp')
        
        if events.exists():
            self.console.print(f"\n[bold yellow]Security Events ({events.count()} total):[/bold yellow]")
            self._display_events_table(events[:10])
        
        # Threat intelligence
        try:
            threat = ThreatIntelligence.objects.get(ip_address=ip)
            self.console.print(f"\n[bold red]Threat Intelligence:[/bold red]")
            threat_table = Table()
            threat_table.add_column("Field", style="cyan")
            threat_table.add_column("Value", style="magenta")
            
            threat_table.add_row("Threat Type", threat.get_threat_type_display())
            threat_table.add_row("Confidence", f"{threat.confidence}%")
            threat_table.add_row("Blocked", "Yes" if threat.blocked else "No")
            threat_table.add_row("Whitelisted", "Yes" if threat.whitelisted else "No")
            threat_table.add_row("Source", threat.source)
            threat_table.add_row("Description", threat.description or "N/A")
            
            self.console.print(threat_table)
        except ThreatIntelligence.DoesNotExist:
            self.console.print("[yellow]No threat intelligence available[/yellow]")
        
        # WHOIS lookup
        try:
            self.console.print(f"\n[bold blue]WHOIS Information:[/bold blue]")
            whois_info = whois.whois(ip)
            if whois_info.org:
                self.console.print(f"Organization: {whois_info.org}")
            if whois_info.country:
                self.console.print(f"Country: {whois_info.country}")
        except Exception:
            self.console.print("[yellow]WHOIS lookup failed[/yellow]")
    
    # Helper methods
    def _apply_event_filters(self, queryset, options):
        """Apply filters to security events queryset"""
        if options.get('hours'):
            since = timezone.now() - timedelta(hours=options['hours'])
            queryset = queryset.filter(timestamp__gte=since)
        
        if options.get('severity'):
            queryset = queryset.filter(severity=options['severity'])
        
        if options.get('event_type'):
            queryset = queryset.filter(event_type__icontains=options['event_type'])
        
        if options.get('ip'):
            queryset = queryset.filter(ip_address__icontains=options['ip'])
        
        if options.get('user'):
            queryset = queryset.filter(user__username__icontains=options['user'])
        
        if options.get('blocked'):
            queryset = queryset.filter(blocked=True)
        
        return queryset
    
    def _display_events_table(self, events):
        """Display security events in table format"""
        if not events:
            self.console.print("[yellow]No events found[/yellow]")
            return
        
        table = Table(title="Security Events")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("IP", style="blue")
        table.add_column("User", style="green")
        table.add_column("Message", style="white")
        table.add_column("Blocked", style="magenta")
        
        for event in events:
            table.add_row(
                event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                event.get_event_type_display(),
                event.severity.upper(),
                event.ip_address,
                event.user.username if event.user else "Anonymous",
                event.message[:50] + "..." if len(event.message) > 50 else event.message,
                "🛑" if event.blocked else "✅"
            )
        
        self.console.print(table)
    
    def _display_threats_table(self, threats):
        """Display threat intelligence in table format"""
        if not threats:
            self.console.print("[yellow]No threats found[/yellow]")
            return
        
        table = Table(title="Threat Intelligence")
        table.add_column("IP Address", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Confidence", style="red")
        table.add_column("Blocked", style="magenta")
        table.add_column("Source", style="green")
        table.add_column("Description", style="white")
        
        for threat in threats:
            table.add_row(
                threat.ip_address,
                threat.get_threat_type_display(),
                f"{threat.confidence}%",
                "🛑" if threat.blocked else "✅" if threat.whitelisted else "⚪",
                threat.source,
                (threat.description or "")[:40] + "..." if threat.description and len(threat.description) > 40 else threat.description or ""
            )
        
        self.console.print(table)
    
    def _display_audit_table(self, logs):
        """Display audit logs in table format"""
        if not logs:
            self.console.print("[yellow]No audit logs found[/yellow]")
            return
        
        table = Table(title="Audit Logs")
        table.add_column("Timestamp", style="cyan")
        table.add_column("User", style="green")
        table.add_column("Action", style="yellow")
        table.add_column("Object", style="blue")
        table.add_column("IP", style="magenta")
        
        for log in logs:
            table.add_row(
                log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                log.user.username if log.user else "System",
                log.get_action_display(),
                log.object_repr[:30] + "..." if len(log.object_repr) > 30 else log.object_repr,
                log.ip_address or "N/A"
            )
        
        self.console.print(table)
    
    def _get_status_icon(self, value, warning_threshold, critical_threshold):
        """Get status icon based on thresholds"""
        if value >= critical_threshold:
            return "🔴"
        elif value >= warning_threshold:
            return "🟡"
        return "🟢"
    
    def _get_severity_status(self, severity, count):
        """Get status for severity levels"""
        if severity in ['critical', 'high'] and count > 0:
            return "🔴"
        elif severity == 'medium' and count > 10:
            return "🟡"
        return "🟢"
    
    def _get_performance_status(self, value):
        """Get performance status icon"""
        if value > 80:
            return "🔴"
        elif value > 60:
            return "🟡"
        return "🟢"
    
    def _show_top_threats(self, limit=5):
        """Show top blocked threats"""
        threats = ThreatIntelligence.objects.filter(blocked=True).order_by('-confidence')[:limit]
        
        if threats:
            self.console.print("\n[bold red]🚨 Top Blocked Threats:[/bold red]")
            self._display_threats_table(threats)
    
    def _show_recent_events(self, events, title):
        """Show recent events with title"""
        if events:
            self.console.print(f"\n[bold yellow]⚠️  {title}:[/bold yellow]")
            self._display_events_table(events)
    
    def _analyze_ip_patterns(self, since, limit):
        """Analyze IP address patterns"""
        ip_stats = SecurityEvent.objects.filter(timestamp__gte=since).values('ip_address').annotate(
            event_count=Count('id'),
            severity_score=Count('id', filter=Q(severity='critical')) * 4 + 
                          Count('id', filter=Q(severity='high')) * 3 +
                          Count('id', filter=Q(severity='medium')) * 2 +
                          Count('id', filter=Q(severity='low')) * 1
        ).order_by('-event_count')[:limit]
        
        if ip_stats:
            self.console.print("\n[bold cyan]🌐 Top Active IP Addresses:[/bold cyan]")
            ip_table = Table()
            ip_table.add_column("IP Address", style="cyan")
            ip_table.add_column("Events", style="magenta")
            ip_table.add_column("Severity Score", style="red")
            ip_table.add_column("Status", style="yellow")
            
            for stat in ip_stats:
                try:
                    threat = ThreatIntelligence.objects.get(ip_address=stat['ip_address'])
                    status = "🛑 BLOCKED" if threat.blocked else "⚪ MONITORING"
                except ThreatIntelligence.DoesNotExist:
                    status = "🔍 NEW"
                
                ip_table.add_row(
                    stat['ip_address'],
                    str(stat['event_count']),
                    str(stat['severity_score']),
                    status
                )
            
            self.console.print(ip_table)
    
    def _analyze_attack_patterns(self, since):
        """Analyze attack patterns"""
        patterns = SecurityEvent.objects.filter(timestamp__gte=since).values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        if patterns:
            self.console.print("\n[bold red]🎯 Attack Patterns:[/bold red]")
            pattern_table = Table()
            pattern_table.add_column("Attack Type", style="red")
            pattern_table.add_column("Occurrences", style="magenta")
            pattern_table.add_column("Trend", style="yellow")
            
            for pattern in patterns:
                # Simple trend analysis - compare with previous period
                prev_period = timezone.now() - timedelta(hours=48)
                prev_count = SecurityEvent.objects.filter(
                    event_type=pattern['event_type'],
                    timestamp__range=(prev_period, since)
                ).count()
                
                if pattern['count'] > prev_count:
                    trend = "📈 INCREASING"
                elif pattern['count'] < prev_count:
                    trend = "📉 DECREASING"
                else:
                    trend = "➡️ STABLE"
                
                pattern_table.add_row(
                    pattern['event_type'],
                    str(pattern['count']),
                    trend
                )
            
            self.console.print(pattern_table)
    
    def _analyze_user_behavior(self, since):
        """Analyze user behavior patterns"""
        user_stats = SecurityEvent.objects.filter(
            timestamp__gte=since,
            user__isnull=False
        ).values('user__username').annotate(
            event_count=Count('id'),
            failed_logins=Count('id', filter=Q(event_type='login_failure')),
            blocked_events=Count('id', filter=Q(blocked=True))
        ).order_by('-event_count')[:10]
        
        if user_stats:
            self.console.print("\n[bold green]👤 User Activity Analysis:[/bold green]")
            user_table = Table()
            user_table.add_column("Username", style="green")
            user_table.add_column("Total Events", style="magenta")
            user_table.add_column("Failed Logins", style="red")
            user_table.add_column("Blocked Events", style="yellow")
            user_table.add_column("Risk Level", style="cyan")
            
            for stat in user_stats:
                # Calculate risk level
                risk_score = stat['failed_logins'] * 2 + stat['blocked_events'] * 3
                if risk_score > 10:
                    risk_level = "🔴 HIGH"
                elif risk_score > 5:
                    risk_level = "🟡 MEDIUM"
                else:
                    risk_level = "🟢 LOW"
                
                user_table.add_row(
                    stat['user__username'],
                    str(stat['event_count']),
                    str(stat['failed_logins']),
                    str(stat['blocked_events']),
                    risk_level
                )
            
            self.console.print(user_table)
    
    def _analyze_geographic_patterns(self, since):
        """Analyze geographic attack patterns"""
        geo_stats = SecurityEvent.objects.filter(
            timestamp__gte=since,
            country_code__isnull=False
        ).values('country_code').annotate(
            event_count=Count('id'),
            unique_ips=Count('ip_address', distinct=True)
        ).order_by('-event_count')[:10]
        
        if geo_stats:
            self.console.print("\n[bold blue]🌍 Geographic Analysis:[/bold blue]")
            geo_table = Table()
            geo_table.add_column("Country", style="blue")
            geo_table.add_column("Events", style="magenta")
            geo_table.add_column("Unique IPs", style="cyan")
            geo_table.add_column("Avg Events/IP", style="yellow")
            
            for stat in geo_stats:
                avg_events = stat['event_count'] / stat['unique_ips'] if stat['unique_ips'] > 0 else 0
                geo_table.add_row(
                    stat['country_code'],
                    str(stat['event_count']),
                    str(stat['unique_ips']),
                    f"{avg_events:.1f}"
                )
            
            self.console.print(geo_table)
    
    def _export_events_json(self, events, output_file):
        """Export events to JSON format"""
        data = []
        for event in events:
            data.append({
                'timestamp': event.timestamp.isoformat(),
                'event_type': event.event_type,
                'severity': event.severity,
                'ip_address': event.ip_address,
                'user': event.user.username if event.user else None,
                'message': event.message,
                'blocked': event.blocked,
                'investigated': event.investigated
            })
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.console.print(f"[green]Exported {len(data)} events to {output_file}[/green]")
        else:
            self.console.print(json.dumps(data, indent=2))
    
    def _export_events_csv(self, events, output_file):
        """Export events to CSV format"""
        fieldnames = [
            'timestamp', 'event_type', 'severity', 'ip_address', 
            'user', 'message', 'blocked', 'investigated'
        ]
        
        if output_file:
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for event in events:
                    writer.writerow({
                        'timestamp': event.timestamp.isoformat(),
                        'event_type': event.event_type,
                        'severity': event.severity,
                        'ip_address': event.ip_address,
                        'user': event.user.username if event.user else '',
                        'message': event.message,
                        'blocked': event.blocked,
                        'investigated': event.investigated
                    })
            
            self.console.print(f"[green]Exported {events.count()} events to {output_file}[/green]")
        else:
            # Print CSV to console
            for event in events:
                self.console.print(",".join([
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.severity,
                    event.ip_address,
                    event.user.username if event.user else '',
                    f'"{event.message}"',
                    str(event.blocked),
                    str(event.investigated)
                ]))