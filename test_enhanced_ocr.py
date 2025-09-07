"""
Test script for the enhanced OCR system with sample bills.
"""
import os
import sys
import json
from enhanced_scanner import EnhancedReceiptScanner
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_ocr():
    """Test the enhanced OCR system with sample bill images."""
    
    # Initialize the enhanced scanner
    logger.info("Initializing Enhanced Receipt Scanner...")
    scanner = EnhancedReceiptScanner()
    
    # Sample images directory
    sample_dir = 'assets/bill_img'
    
    if not os.path.exists(sample_dir):
        logger.error(f"Sample directory not found: {sample_dir}")
        return
    
    # Get all image files
    image_files = [f for f in os.listdir(sample_dir) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'))]
    
    if not image_files:
        logger.error("No image files found in sample directory")
        return
    
    logger.info(f"Found {len(image_files)} sample images")
    
    results = []
    
    for i, image_file in enumerate(image_files, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {i}/{len(image_files)}: {image_file}")
        logger.info(f"{'='*60}")
        
        try:
            image_path = os.path.join(sample_dir, image_file)
            
            # Scan the receipt
            extracted_data = scanner.scan_receipt(image_path, save_processed=True)
            
            # Display results
            print(f"\n📄 RESULTS FOR: {image_file}")
            print(f"{'─'*50}")
            print(f"🏪 Merchant: {extracted_data.merchant or 'Not detected'}")
            print(f"📅 Date: {extracted_data.date or 'Not detected'}")
            print(f"💰 Total: ₹{extracted_data.total or 'Not detected'}")
            print(f"💸 Tax: ₹{extracted_data.tax or 'Not detected'}")
            print(f"🧾 Receipt #: {extracted_data.receipt_number or 'Not detected'}")
            print(f"💳 Payment: {extracted_data.payment_method or 'Not detected'}")
            print(f"📊 Confidence: {extracted_data.confidence_score:.1%}")
            
            if extracted_data.items:
                print(f"\n🛒 ITEMS ({len(extracted_data.items)}):")
                for j, item in enumerate(extracted_data.items, 1):
                    name = item.get('name', 'Unknown')
                    qty = item.get('quantity', 1)
                    price = item.get('unit_price', 0)
                    total = item.get('total_price', price)
                    print(f"  {j}. {name}")
                    print(f"     Qty: {qty} | Price: ₹{price} | Total: ₹{total}")
            else:
                print("\n🛒 ITEMS: None detected")
            
            # Store result
            result = {
                'file': image_file,
                'success': True,
                'data': {
                    'merchant': extracted_data.merchant,
                    'date': extracted_data.date,
                    'total': extracted_data.total,
                    'tax': extracted_data.tax,
                    'items': extracted_data.items,
                    'receipt_number': extracted_data.receipt_number,
                    'payment_method': extracted_data.payment_method,
                    'confidence_score': extracted_data.confidence_score
                }
            }
            results.append(result)
            
            print(f"\n✅ Processing completed successfully!")
            
        except Exception as e:
            logger.error(f"Error processing {image_file}: {str(e)}")
            print(f"\n❌ Error: {str(e)}")
            
            results.append({
                'file': image_file,
                'success': False,
                'error': str(e)
            })
    
    # Save comprehensive results
    results_file = 'data/test_results.json'
    os.makedirs('data', exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"Total files processed: {len(results)}")
    print(f"Successful extractions: {successful}")
    print(f"Failed extractions: {len(results) - successful}")
    print(f"Success rate: {successful/len(results):.1%}")
    print(f"\nResults saved to: {results_file}")
    print(f"Processed images saved to: data/processed/")

if __name__ == "__main__":
    test_enhanced_ocr()
