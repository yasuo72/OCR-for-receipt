from django.contrib import admin
from django.utils.html import format_html
from scanner.models import Receipt, ReceiptItem


class ReceiptItemInline(admin.TabularInline):
    model = ReceiptItem
    extra = 0
    fields = ('name', 'quantity', 'unit_price', 'total_price', 'hsn_code', 'tax_rate', 'category')


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'merchant',
        'date',
        'formatted_total',
        'formatted_tax',
        'confidence_badge',
        'scanner_method',
        'status_badge',
        'created_at'
    )
    list_filter = ('status', 'scanner_method', 'created_at')
    search_fields = ('merchant', 'filename', 'raw_text', 'receipt_number', 'payment_method')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    inlines = [ReceiptItemInline]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Receipt Overview', {
            'fields': ('filename', 'merchant', 'date', 'status', 'scanner_method')
        }),
        ('Financial Details', {
            'fields': ('total', 'subtotal', 'tax', 'payment_method', 'receipt_number')
        }),
        ('OCR Data & Confidence', {
            'fields': ('confidence_score', 'raw_text')
        }),
        ('Images', {
            'fields': ('image', 'processed_image', 'image_preview')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def formatted_total(self, obj):
        return f"₹{obj.total:.2f}" if obj.total is not None else "—"
    formatted_total.short_description = "Total"
    formatted_total.admin_order_field = "total"

    def formatted_tax(self, obj):
        return f"₹{obj.tax:.2f}" if obj.tax is not None else "—"
    formatted_tax.short_description = "Tax"

    def confidence_badge(self, obj):
        pct = (obj.confidence_score or 0) * 100
        color = "#10b981" if pct >= 75 else "#f59e0b" if pct >= 50 else "#ef4444"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{:.1f}%</span>',
            color, pct
        )
    confidence_badge.short_description = "Confidence"
    confidence_badge.admin_order_field = "confidence_score"

    def status_badge(self, obj):
        color_map = {
            'processed': '#10b981',
            'processing': '#3b82f6',
            'uploaded': '#6366f1',
            'failed': '#ef4444'
        }
        color = color_map.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; text-transform: uppercase;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 250px; border-radius: 6px; border: 1px solid #ccc;" />', obj.image.url)
        return "No image uploaded"
    image_preview.short_description = "Image Preview"


@admin.register(ReceiptItem)
class ReceiptItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'receipt', 'quantity', 'formatted_price', 'formatted_total', 'hsn_code', 'category')
    search_fields = ('name', 'receipt__merchant', 'hsn_code')
    list_filter = ('category',)

    def formatted_price(self, obj):
        return f"₹{obj.unit_price:.2f}"
    formatted_price.short_description = "Unit Price"

    def formatted_total(self, obj):
        return f"₹{obj.total_price:.2f}"
    formatted_total.short_description = "Total Price"
