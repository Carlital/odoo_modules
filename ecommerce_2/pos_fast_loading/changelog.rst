Changelog
=========

1.1.0(9 Jan'26)
------------------

- **Remove syncing of Pricelist**
 - Now there is no need to sync the pricelist. It automatically syncs the required pricelist.

- **Partner Loading Optimized**
 - Improved the logic to load the partner from mongo and postgres to make it faster.

- **Fixed Mongo data load**
 - Issues related to syncing data from the mongo has been fixed.

- **Sync from Cron**
 - This is added to sync the data when there is large data set.

- **Code Optimized**
 - Unwanted codes are removed and Code formatting is done. 


1.0.4(29 Oct'25)
------------------

- **requirement.txt**
 - Added requirement.txt file


1.0.3(8 July'25)
------------------

- **load Prods IndexDB**
 - Fixed the issue related to load product in the IndexedDB


1.0.2 (13 May'25)
------------------

- **Category-Restricted Product Loading** 
 - Now loads only products belonging to configured restricted categories when the restriction is enabled, optimizing performance.

- **IndexedDB Improvements**
 - Fixed product loading from IndexedDB.
 - Created separate IndexedDB stores for each POS config to manage product data and last update timestamps independently.

- **Real-Time Sync Enhancements**
 - Fixed real-time notifications between MongoDB and PostgreSQL to properly reflect backend record changes.
 - Realtime pricelist updates now correctly sync on notification and backend changes.

- **Stability & Performance** 
 - Several backend optimizations to improve sync reliability and reduce redundant data processing.

- **Code Optimization** code refracted and improved file structure.

1.0.1 (21 Jan'25)
------------------
- Added Multi Company compatibility feature.

1.0.0 (16 Oct'24)
------------------
- Initial release for POS Fast loading.
- Fast loading of products, customers and pricelist with realtime sync feature.
