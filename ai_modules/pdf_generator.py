"""
PDF Report Generator - FIXED AND TESTED
Save as: ai_modules/pdf_generator.py
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import base64
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Generate PDF reports with charts and data tables"""
    
    @staticmethod
    def _decode_base64_image(base64_data):
        """
        Safely decode base64 image data
        Handles both raw base64 and data URI formats
        """
        try:
            # Remove data URI prefix if present
            if isinstance(base64_data, str):
                if base64_data.startswith('data:image'):
                    # Format: data:image/png;base64,<base64data>
                    base64_data = base64_data.split(',')[1]
                
                # Decode and return BytesIO
                image_bytes = base64.b64decode(base64_data)
                return BytesIO(image_bytes)
        except Exception as e:
            logger.error(f"Error decoding base64 image: {str(e)}")
            return None
    
    @staticmethod
    def generate_report_pdf(report_data, report_type, charts_base64=None):
        """
        Generate a PDF report from report data and charts
        
        Args:
            report_data: Dictionary containing report data
            report_type: Type of report (monthly, quarterly, comparison, custom)
            charts_base64: Dictionary with chart images as base64
        
        Returns:
            BytesIO object containing PDF or None on error
        """
        try:
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            
            # Get styles
            styles = getSampleStyleSheet()
            custom_styles = PDFGenerator._get_custom_styles()
            
            # Build document
            story = []
            
            # Validate report data
            if not report_data:
                raise ValueError("Report data is empty")
            
            # Add header
            story.extend(PDFGenerator._build_header(report_data, report_type, custom_styles))
            
            # Add summary section
            story.append(Spacer(1, 0.3*inch))
            story.extend(PDFGenerator._build_summary(report_data, report_type, custom_styles))
            
            # Add charts if available and valid
            if charts_base64 and isinstance(charts_base64, dict) and len(charts_base64) > 0:
                story.append(Spacer(1, 0.3*inch))
                charts_section = PDFGenerator._build_charts_section(charts_base64, custom_styles)
                if charts_section:  # Only add if charts were successfully built
                    story.extend(charts_section)
            
            # Add data tables
            story.append(Spacer(1, 0.3*inch))
            story.extend(PDFGenerator._build_tables_section(report_data, report_type, custom_styles))
            
            # Add footer
            story.append(Spacer(1, 0.3*inch))
            story.extend(PDFGenerator._build_footer(custom_styles))
            
            # Build PDF
            doc.build(story)
            pdf_buffer.seek(0)
            
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    @staticmethod
    def _get_custom_styles():
        """Define custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#6B7280'),
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1F2937'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceAfter=6
        )
        
        return {
            'title': title_style,
            'subtitle': subtitle_style,
            'section': section_style,
            'normal': normal_style
        }
    
    @staticmethod
    def _build_header(report_data, report_type, styles):
        """Build PDF header section with validation"""
        story = []
        
        try:
            period = report_data.get('period', {})
            
            if report_type == 'monthly':
                title = f"{period.get('month_name', 'Report')} {period.get('year', '')} Financial Report"
                date_range = f"{period.get('start_date', '')} to {period.get('end_date', '')}"
            elif report_type == 'quarterly':
                title = f"Q{period.get('quarter', '')} {period.get('year', '')} Financial Report"
                date_range = f"{period.get('start_date', '')} to {period.get('end_date', '')}"
            elif report_type == 'custom':
                title = "Custom Range Financial Report"
                date_range = f"{period.get('start_date', '')} to {period.get('end_date', '')}"
            else:
                title = "Financial Report Comparison"
                date_range = f"Generated on {datetime.now().strftime('%B %d, %Y')}"
            
            story.append(Paragraph(title, styles['title']))
            story.append(Paragraph(date_range, styles['subtitle']))
            
        except Exception as e:
            logger.error(f"Error building header: {str(e)}")
            story.append(Paragraph("Financial Report", styles['title']))
        
        return story
    
    @staticmethod
    def _build_summary(report_data, report_type, styles):
        """Build summary section with dynamic data"""
        story = []
        
        try:
            summary = report_data.get('summary', {})
            
            if not summary:
                return story
            
            story.append(Paragraph("Summary", styles['section']))
            
            # Build summary table dynamically
            summary_data = [['Metric', 'Value']]
            
            # Add metrics only if they exist and have values
            metrics = [
                ('Total Expenses', 'total_expenses', '₹{:,.2f}'),
                ('Transaction Count', 'transaction_count', '{}'),
                ('Average Transaction', 'average_transaction', '₹{:,.2f}'),
                ('Daily Average', 'average_daily', '₹{:,.2f}'),
                ('Total Tax', 'total_tax', '₹{:,.2f}'),
                ('Average Monthly', 'average_monthly', '₹{:,.2f}'),
                ('Days in Period', 'days_in_period', '{}'),
            ]
            
            for label, key, format_str in metrics:
                value = summary.get(key)
                if value is not None and value != 0:
                    try:
                        formatted_value = format_str.format(float(value) if isinstance(value, (int, float)) else value)
                        summary_data.append([label, formatted_value])
                    except (ValueError, TypeError):
                        logger.warning(f"Could not format {key}: {value}")
            
            # Create summary table
            if len(summary_data) > 1:
                t = Table(summary_data, colWidths=[3.5*inch, 2*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                
                story.append(t)
        
        except Exception as e:
            logger.error(f"Error building summary: {str(e)}")
        
        return story
    
    @staticmethod
    def _build_charts_section(charts_base64, styles):
        """Build charts section with proper error handling"""
        story = []
        
        if not charts_base64:
            return story
        
        charts_added = False
        
        for chart_name, chart_data in charts_base64.items():
            if not chart_data:
                continue
            
            try:
                # Decode base64 image
                image_buffer = PDFGenerator._decode_base64_image(chart_data)
                
                if image_buffer is None:
                    logger.warning(f"Could not decode chart image: {chart_name}")
                    continue
                
                # Add header only once
                if not charts_added:
                    story.append(Paragraph("Charts & Visualizations", styles['section']))
                    charts_added = True
                
                # Create image with proper sizing
                img = Image(image_buffer, width=6*inch, height=3*inch)
                
                # Format chart name for display
                display_name = chart_name.replace('_', ' ').title()
                story.append(Paragraph(display_name, styles['normal']))
                story.append(img)
                story.append(Spacer(1, 0.2*inch))
                
            except Exception as e:
                logger.error(f"Error adding chart {chart_name}: {str(e)}")
                # Continue with next chart instead of failing entirely
                continue
        
        return story
    
    @staticmethod
    def _build_tables_section(report_data, report_type, styles):
        """Build data tables section with validation"""
        story = []
        
        try:
            # Categories table
            categories = report_data.get('categories', [])
            if categories and len(categories) > 0:
                story.append(Paragraph("Category Breakdown", styles['section']))
                
                categories_data = [['Category', 'Amount', 'Transactions', 'Percentage']]
                
                for cat in categories[:10]:
                    try:
                        categories_data.append([
                            str(cat.get('name', 'Unknown')),
                            f"₹{float(cat.get('total', 0)):,.2f}",
                            str(cat.get('count', 0)),
                            f"{float(cat.get('percentage', 0)):.1f}%"
                        ])
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"Error processing category: {str(e)}")
                        continue
                
                t = Table(categories_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                
                story.append(t)
                story.append(Spacer(1, 0.2*inch))
        
        except Exception as e:
            logger.error(f"Error building categories table: {str(e)}")
        
        # Vendors table
        try:
            vendors = report_data.get('vendors', [])
            if vendors and len(vendors) > 0:
                story.append(PageBreak())
                story.append(Paragraph("Top Vendors", styles['section']))
                
                vendors_data = [['Vendor', 'Amount', 'Transactions']]
                for vendor in vendors[:10]:
                    try:
                        vendors_data.append([
                            str(vendor.get('name', 'Unknown')),
                            f"₹{float(vendor.get('total', 0)):,.2f}",
                            str(vendor.get('count', 0))
                        ])
                    except (KeyError, ValueError, TypeError):
                        continue
                
                t = Table(vendors_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                ]))
                
                story.append(t)
                story.append(Spacer(1, 0.2*inch))
        
        except Exception as e:
            logger.error(f"Error building vendors table: {str(e)}")
        
        # Monthly breakdown for quarterly reports
        try:
            if report_type == 'quarterly':
                monthly = report_data.get('monthly_breakdown', [])
                if monthly and len(monthly) > 0:
                    story.append(PageBreak())
                    story.append(Paragraph("Monthly Breakdown", styles['section']))
                    
                    monthly_data = [['Month', 'Total Spent', 'Transactions']]
                    for month in monthly:
                        try:
                            monthly_data.append([
                                str(month.get('month_name', 'Unknown')),
                                f"₹{float(month.get('total', 0)):,.2f}",
                                str(month.get('count', 0))
                            ])
                        except (KeyError, ValueError, TypeError):
                            continue
                    
                    t = Table(monthly_data, colWidths=[2*inch, 2*inch, 2*inch])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    
                    story.append(t)
                    story.append(Spacer(1, 0.2*inch))
        
        except Exception as e:
            logger.error(f"Error building monthly breakdown: {str(e)}")
        
        # Period comparison for comparison reports
        try:
            if report_type == 'comparison':
                data = report_data.get('data', [])
                if data and len(data) > 0:
                    story.append(PageBreak())
                    story.append(Paragraph("Period Comparison", styles['section']))
                    
                    comparison_data = [['Period', 'Total Spent', 'Transactions', 'Avg Transaction']]
                    for period in data:
                        try:
                            comparison_data.append([
                                str(period.get('period', 'Unknown')),
                                f"₹{float(period.get('total', 0)):,.2f}",
                                str(period.get('count', 0)),
                                f"₹{float(period.get('avg_transaction', 0)):,.2f}"
                            ])
                        except (KeyError, ValueError, TypeError):
                            continue
                    
                    t = Table(comparison_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
                        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
                    ]))
                    
                    story.append(t)
                    story.append(Spacer(1, 0.2*inch))
        
        except Exception as e:
            logger.error(f"Error building comparison table: {str(e)}")
        
        return story
    
    @staticmethod
    def _build_footer(styles):
        """Build PDF footer section"""
        story = []
        
        try:
            footer_text = f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')} | Finance AI Report System"
            story.append(Spacer(1, 0.2*inch))
            
            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['normal'],
                fontSize=8,
                textColor=colors.HexColor('#9CA3AF'),
                alignment=TA_CENTER
            )
            
            story.append(Paragraph(footer_text, footer_style))
        
        except Exception as e:
            logger.error(f"Error building footer: {str(e)}")
        
        return story