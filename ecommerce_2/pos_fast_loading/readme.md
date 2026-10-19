# POS Fast loading (pos_fast_loading)

## Overview
This module is used to load the data fast into pos. It can load more than 1 Lac products and 50k customers in just few seconds. 

## Features

### High-Performance POS Data Loading
  - Load massive datasets (products, customers, pricelists) efficiently.
  - Supports both PostgreSQL and MongoDB as data sources.
  - Offers customizable batch limits to control the number of records processed per batch.

### Flexible Synchronization Configuration
  - Configure what to sync: Products, Customers, Pricelist Items.
  - Choose how to sync:
    - Real-time updates using long polling.
    - Notification-based reload prompts.
    - Manual reload of PoS session.

### Common Changes Tracking
  - Automatically tracks and logs product, customer, and pricelist changes in the backend.
  - Common change records are created for any updates, deletions, or additions.
  - Optimized for fast diffing to sync only necessary updates to the POS frontend.

### Configurable Field Selection
  - Add or exclude specific fields for:
    - Products
    - Customers
    - Pricelist Items

## Installation

### Option 1: Using Custom Addons Directory
1. Place the `pos_fast_loading` module folder inside your custom-addons directory.
2. Restart your Odoo instance to make the module available.

## Configuration

1. **POS Sync Settings**:
  - Navigate to Point of Sale → Configuration → POS Fast Loading Settings.
  - Enable syncing for:
    - Products
    - Customers
    - Pricelist Items

2. **Batch Record Limit**:
  - Set the maximum number of records to be fetched in a single batch (default: 1000).
  - Useful for controlling memory and processing time on slower devices.

3. **Backend Change Handling**:
  - Choose how POS should handle backend data changes:
    - Manual Reload: Prompt user to reload session.
    - Notify and Reload: Notify and allow optional reload.
    - Real-Time Sync: Automatically push updates to the POS.

## Benefits
- Fast POS Load Times: Even for large datasets (100k+ products).
- Smart Sync Options: Fine-grained control over what and how data syncs.
- Compatible with MongoDB: Offers Mongo DB flexibility.
- Full Visibility: View change logs and common changes to track sync accuracy.
- Highly Configurable: Set limits, fields, and sync strategies based on business needs.

### Credits
- **Author**: Webkul Software Pvt. Ltd.