# Bookstore — Glossary

*Sample ubiquitous language for a fictional `bookstore-demo` repo. Import this page into your AppFlowy
workspace as a child of your registry index, then add its `view_id` to the `bookstore-demo` row so
`/load-domain-context` (or the SessionStart hook) injects it. Purely illustrative — safe to delete.*

**Title**: A distinct work that can be sold, identified by ISBN. One Title may have many physical
Copies. Not to be confused with a Listing.

**Copy**: A single physical or digital instance of a Title held in Inventory. A Copy is what a
customer actually receives when an Order ships.

**Listing**: A Title offered for sale at a specific Price and condition. The same Title can have
several Listings (new, used, signed); the storefront shows Listings, not raw Titles.

**Order**: A customer's confirmed purchase of one or more Listings. Moves through the states
`placed → paid → picked → shipped → delivered` (or `cancelled` / `refunded`).

**Fulfilment**: The process of turning a paid Order into a shipment — picking Copies from Inventory,
packing, and handing off to a Carrier. Distinct from the Order itself.

**Shelf**: A location in the warehouse where Copies live. Inventory counts are per-Shelf; a Title's
availability is the sum of on-hand Copies across Shelves minus reserved Copies.

**Reservation**: A hold placed on a Copy the moment an Order is paid, so two customers can't be sold
the last Copy. Released on cancellation or when the shipment is confirmed.
