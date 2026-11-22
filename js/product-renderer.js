/**
 * MOJOWAY Product Card Renderer v1.1
 * ====================================
 * Dynamically renders product cards from MOJOWAY_PRODUCTS data.
 * 
 * v1.1 CHANGE: All buttons now include inline styles as defensive measure.
 *   Even if page CSS fails to load or is cached incorrectly,
 *   buttons will still render as styled buttons, not plain text.
 * 
 * Source of truth: backend/products.json -> js/products_data.js
 * 
 * Usage:
 *   1. Include <script src="/js/products_data.js"></script> BEFORE this script
 *   2. Include <script src="/js/product-renderer.js"></script>
 *   3. Add render containers: <div data-mj-render="pricing"></div>
 * 
 * Supported modes: pricing | pricing-compact | coach-pro | org-mirror
 * 
 * DO NOT EDIT PRODUCT CARDS IN HTML. Edit backend/products.json and run:
 *   python3 backend/scripts/build_products.py
 */

(function() {
  'use strict';

  // -- Data Source --
  // window.MOJOWAY_PRODUCTS is an object: {version, last_updated, products: [...]}
  // Extract the products array (renderer needs to iterate products, not the wrapper).
  var _DATA = window.MOJOWAY_PRODUCTS;
  var PRODUCTS = Array.isArray(_DATA) ? _DATA : ((_DATA && _DATA.products && _DATA.products.length) ? _DATA.products : []);

  if (!PRODUCTS.length) {
    console.warn('[MOJOWAY] No product data loaded. Ensure products_data.js is included before product-renderer.js.');
    return;
  }

  // -- Product Lookup --
  function getProduct(id) {
    for (var i = 0; i < PRODUCTS.length; i++) {
      if (PRODUCTS[i].id === id) return PRODUCTS[i];
    }
    return null;
  }

  function getProductByName(name) {
    for (var i = 0; i < PRODUCTS.length; i++) {
      if (PRODUCTS[i].name === name) return PRODUCTS[i];
    }
    return null;
  }

  // -- HTML Helpers --
  function esc(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // -- Inline Style Constants (defensive: buttons always render styled) --
  var STYLE_PRIMARY = 'display:block; background:#c9a96e; color:#1A1F2E; padding:12px 24px; border-radius:8px; font-weight:600; font-size:0.85rem; text-decoration:none; text-align:center; width:100%; box-sizing:border-box; border:none; cursor:pointer; margin-top:auto; transition:all 0.2s ease; line-height:1.4;';
  var STYLE_SECONDARY = 'display:block; background:rgba(0,0,0,0.04); color:#1A1F2E; padding:12px 24px; border-radius:8px; font-weight:600; font-size:0.85rem; text-decoration:none; text-align:center; width:100%; box-sizing:border-box; border:1px solid rgba(0,0,0,0.1); cursor:pointer; margin-top:8px; line-height:1.4;';
  var STYLE_CARD_CTA = 'display:block; background:#c9a96e; color:#1A1F2E; padding:14px 24px; border-radius:8px; font-weight:600; font-size:0.95rem; text-decoration:none; text-align:center; width:100%; box-sizing:border-box; border:none; cursor:pointer; margin-top:16px; line-height:1.4;';

  function badgeHTML(product) {
    if (!product.badge) return '';
    var cls = product.badge_style === 'green' ? 'plan-badge green' : 'plan-badge';
    var style = 'display:inline-block; padding:4px 12px; border-radius:20px; font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; background:rgba(201,169,110,0.15); color:#c9a96e; margin-bottom:8px;';
    return '<div class="' + cls + '" style="' + style + '">' + esc(product.badge) + '</div>';
  }

  function featuresHTML(product) {
    var html = '<ul class="plan-features" style="list-style:none; padding:0; margin:0 0 24px; flex:1;">';
    var features = product.features || [];
    for (var i = 0; i < features.length; i++) {
      html += '<li style="padding:6px 0; font-size:0.85rem; color:rgba(26,31,46,0.7); border-bottom:1px solid rgba(26,31,46,0.04); display:flex; align-items:flex-start; gap:8px; line-height:1.5;"><span style="color:#c9a96e; opacity:0.5; flex-shrink:0;">&mdash;</span>' + esc(features[i]) + '</li>';
    }
    html += '</ul>';
    return html;
  }

  function ctaHTML(product) {
    var btnClass = product.cta_style || 'primary';
    var cls = 'plan-btn ' + btnClass;
    var style = (btnClass === 'secondary') ? STYLE_SECONDARY : STYLE_PRIMARY;
    // Prefer cta_link (the free-trial entry point); fall back to stripe_link
    var href = product.cta_link || product.stripe_link;
    var html = '<a href="' + esc(href) + '" class="' + cls + '" style="' + style + '">' + esc(product.cta_text) + '</a>';
    
    // Secondary CTA button (e.g., Free Team Diagnosis for Org Mirror) — light theme
    if (product.secondary_cta_text && product.secondary_cta_link) {
      var secondaryStyle = 'display:block; background:rgba(0,0,0,0.04); color:#1A1F2E; padding:12px 24px; border-radius:8px; font-weight:600; font-size:0.85rem; text-decoration:none; text-align:center; width:100%; box-sizing:border-box; border:1px solid rgba(0,0,0,0.1); cursor:pointer; margin-top:8px; line-height:1.4;';
      html += '\n      <a href="' + esc(product.secondary_cta_link) + '" class="plan-btn secondary" style="' + secondaryStyle + '">' + esc(product.secondary_cta_text) + '</a>';
    }
    
    return html;
  }

  // -- Card Builder: Pricing Page --
  function renderPricingCard(product) {
    var extraClass = product.plan_extra_class || '';
    var idAttr = product.plan_id ? ' id="' + esc(product.plan_id) + '"' : '';
    
    // Card container with inline style fallback (light theme — matches pricing.html CSS)
    var cardStyle = 'display:flex; flex-direction:column; background:#FFFFFF; border:1px solid rgba(0,0,0,0.08); border-radius:16px; padding:28px 24px 32px; position:relative; transition:transform 0.3s ease, box-shadow 0.3s ease; box-shadow:0 4px 24px rgba(0,0,0,0.06);';
    if (extraClass === 'organization' || extraClass === 'featured') {
      cardStyle += ' border-color:rgba(201,169,110,0.3); background:rgba(201,169,110,0.06);';
    }
    
    var html = '<div class="plan ' + extraClass + '"' + idAttr + ' style="' + cardStyle + '">\n';
    html += '      ' + badgeHTML(product) + '\n';
    html += '      <div class="plan-name" style="font-family:Georgia,serif; font-size:1.3rem; font-weight:400; color:#1A1F2E; margin:0 0 4px;">' + esc(product.name) + '</div>\n';
    html += '      <div class="plan-price" style="font-size:2rem; font-weight:600; color:#c9a96e; margin:8px 0 2px; letter-spacing:-0.5px;">' + esc(product.price) + ' <span style="font-size:0.8rem; color:rgba(26,31,46,0.4); font-weight:400;">' + esc(product.price_type) + '</span></div>\n';
    
    if (product.price_sub) {
      html += '      <div class="plan-price-sub" style="font-size:0.75rem; color:rgba(26,31,46,0.4); margin-bottom:16px;">' + esc(product.price_sub) + '</div>\n';
    }
    // Annual anchor (matches the homepage; links straight to annual checkout)
    if (product.annual_price && product.annual_stripe_link) {
      html += '      <a href="' + esc(product.annual_stripe_link) + '" style="display:inline-block; font-size:0.8rem; color:#8a6d3b; margin-bottom:16px; text-decoration:underline;">or ' + esc(product.annual_price) + ' (save 34%)</a>\n';
    }
    
    html += '      <div class="plan-desc" style="font-size:0.85rem; color:rgba(26,31,46,0.6); margin-bottom:16px; line-height:1.5;">' + esc(product.description) + '</div>\n';
    html += '      ' + featuresHTML(product) + '\n';
    html += '      ' + ctaHTML(product) + '\n';
    html += '    </div>';
    
    return html;
  }

  // -- Card Builder: Index Page (compact) --
  // v1.2: Mirror-led — the card shows one hook benefit; the rest fold into "Full details"
  var __cardSeq = 0;
  function renderPricingCompactCard(product) {
    var isFeatured = product.featured ? ' featured' : '';
    var priceLabel = product.price_type === 'one-time' ? '' : '/' + product.price_type;
    // CTA link: prefer cta_link (free-trial entry, e.g. Mirror); fall back to stripe_link
    var ctaHref = product.cta_link || product.stripe_link;
    var cardId = 'mj-feat-' + (++__cardSeq);
    var btnId = 'mj-btn-' + __cardSeq;
    
    var cardStyle = 'display:flex; flex-direction:column; background:#fff; border:1px solid #e8e5e0; border-radius:12px; padding:28px 20px; transition:transform 0.2s ease, box-shadow 0.2s ease;';
    if (isFeatured) {
      cardStyle = 'display:flex; flex-direction:column; background:#fff; border:2px solid #c9a96e; border-radius:12px; padding:28px 20px; transition:transform 0.2s ease, box-shadow 0.2s ease;';
    }
    
    var html = '<div class="pricing-card' + isFeatured + '" style="' + cardStyle + '">\n';
    html += '      <p class="card-name" style="font-family:Georgia,serif; font-size:1.1rem; font-weight:600; color:#2a2a2a; margin:0 0 8px 0;">' + esc(product.name) + '</p>\n';
    html += '      <div class="card-price" style="font-size:1.8rem; font-weight:600; color:#c9a96e; margin-bottom:4px;">' + esc(product.price) + '<span style="font-size:0.8rem; color:#999; font-weight:400;">' + esc(priceLabel) + '</span></div>\n';
    
    if (product.price_sub) {
      html += '      <p class="card-period" style="font-size:0.8rem; color:#888; margin:0 0 12px 0;">' + esc(product.price_sub) + '</p>\n';
    }
    // Annual anchor (shown only when an annual link exists; links to annual checkout)
    if (product.annual_price && product.annual_stripe_link) {
      html += '      <a href="' + esc(product.annual_stripe_link) + '" class="card-annual" style="display:inline-block; font-size:0.8rem; color:#8a6d3b; margin:0 0 12px 0; text-decoration:underline;">or ' + esc(product.annual_price) + ' (save 34%)</a>\n';
    }
    
    // Hook benefit: show only the first one; fold the rest
    var features = product.features || [];
    if (features.length) {
      html += '      <ul class="card-features" style="list-style:none; padding:0; margin:12px 0 4px; flex-grow:1;">\n';
      html += '        <li style="padding:4px 0; font-size:0.85rem; color:#555; position:relative; padding-left:18px;"><span style="position:absolute; left:0; color:#c9a96e;">&mdash;</span>' + esc(features[0]) + '</li>\n';
      html += '      </ul>\n';
      if (features.length > 1) {
        html += '      <div id="' + cardId + '" style="display:none;">\n';
        html += '        <ul class="card-features" style="list-style:none; padding:0; margin:4px 0; flex-grow:1;">\n';
        for (var i = 1; i < features.length; i++) {
          html += '          <li style="padding:4px 0; font-size:0.85rem; color:#555; position:relative; padding-left:18px;"><span style="position:absolute; left:0; color:#c9a96e;">&mdash;</span>' + esc(features[i]) + '</li>\n';
        }
        html += '        </ul>\n';
        html += '      </div>\n';
        html += '      <button type="button" id="' + btnId + '" onclick="window.toggleMjFeatures(\'' + cardId + '\', \'' + btnId + '\')" style="background:none; border:none; padding:6px 0; margin:0 0 16px; cursor:pointer; font-size:0.78rem; color:#8a6d3b; text-decoration:underline; text-align:left;">Full details &darr;</button>\n';
      }
    }
    
    html += '      <a href="' + esc(ctaHref) + '" class="card-cta" style="' + STYLE_CARD_CTA + '">' + esc(product.cta_text) + '</a>\n';
    html += '    </div>';
    
    return html;
  }

  // -- Card Builder: Coach Pro (coaches.html) --
  function renderCoachProCard(product) {
    var cardStyle = 'display:flex; flex-direction:column; background:#fff; border:2px solid #c9a96e; border-radius:12px; padding:28px 20px; max-width:420px; margin:0 auto;';
    
    var html = '<div class="pricing-card featured" style="' + cardStyle + '">\n';
    html += '      <p class="card-name" style="font-family:Georgia,serif; font-size:1.1rem; font-weight:600; color:#2a2a2a; margin:0 0 8px 0;">' + esc(product.name) + '</p>\n';
    html += '      <div class="card-price" style="font-size:1.8rem; font-weight:600; color:#c9a96e; margin-bottom:4px;">' + esc(product.price) + '<span style="font-size:0.8rem; color:#999; font-weight:400;">/month</span></div>\n';
    
    if (product.price_sub) {
      html += '      <p class="card-period" style="font-size:0.8rem; color:#888; margin:0 0 12px 0;">' + esc(product.price_sub) + '</p>\n';
    }
    
    if (product.features && product.features.length) {
      html += '      <ul class="card-features" style="list-style:none; padding:0; margin:12px 0; flex-grow:1;">\n';
      for (var i = 0; i < product.features.length; i++) {
        html += '        <li style="padding:4px 0; font-size:0.85rem; color:#555; position:relative; padding-left:18px;"><span style="position:absolute; left:0; color:#c9a96e;">&mdash;</span>' + esc(product.features[i]) + '</li>\n';
      }
      html += '      </ul>\n';
    }
    
    html += '      <a href="' + esc(product.stripe_link) + '" class="card-cta" style="' + STYLE_CARD_CTA + '">' + esc(product.cta_text) + '</a>\n';
    html += '    </div>';
    
    return html;
  }

  // -- Card Builder: Organization Mirror (organization.html layout) --
  function renderOrgMirrorCard(product) {
    var priceLabel = product.price_type === 'yearly' ? '/year' : '/' + product.price_type;
    var usersNote = product.users_included ? 'Up to ' + product.users_included + ' users included' : '';
    
    var html = '<div class="ent-price-card" style="background:#fff; border:1px solid #e8e5e0; border-radius:12px; padding:32px; max-width:520px; margin:0 auto;">\n';
    html += '      <h3 style="font-family:Georgia,serif; font-size:1.4rem; color:#2a2a2a; margin:0 0 8px 0;">' + esc(product.name) + ' Plan</h3>\n';
    html += '      <div class="ent-price" style="font-size:2.2rem; font-weight:600; color:#c9a96e; margin-bottom:4px;">' + esc(product.price) + '<span style="font-size:1rem; color:#999; font-weight:400;">' + esc(priceLabel) + '</span></div>\n';
    
    if (usersNote) {
      html += '      <p class="ent-price-note" style="font-size:0.85rem; color:#888; margin:0 0 16px 0;">' + esc(usersNote) + '</p>\n';
    }
    
    if (product.features && product.features.length) {
      html += '      <ul class="ent-feature-list" style="list-style:none; padding:0; margin:16px 0;">\n';
      for (var i = 0; i < product.features.length; i++) {
        html += '        <li style="padding:6px 0; font-size:0.9rem; color:#555; position:relative; padding-left:20px;"><span style="position:absolute; left:0; color:#c9a96e;">&mdash;</span>' + esc(product.features[i]) + '</li>\n';
      }
      html += '      </ul>\n';
    }
    
    // Primary CTA - with full inline styles
    var ctaLabel = product.org_cta_text || ('Start ' + esc(product.name) + ' — ' + esc(product.price) + '/' + product.price_type);
    html += '      <a href="' + esc(product.stripe_link) + '" class="btn btn-primary" target="_blank" rel="noopener noreferrer" style="display:block; width:100%; font-size:16px; padding:16px 32px; margin-bottom:12px; background:#c9a96e; color:#12121a; border:none; border-radius:8px; font-weight:600; text-decoration:none; text-align:center; cursor:pointer; box-sizing:border-box; line-height:1.4;">' + esc(ctaLabel) + '</a>\n';
    
    // Secondary CTA — light theme
    if (product.secondary_cta_text && product.secondary_cta_link) {
      html += '      <a href="' + esc(product.secondary_cta_link) + '" class="btn btn-primary" style="display:block; width:100%; font-size:16px; padding:16px 32px; background:rgba(0,0,0,0.04); color:#1A1F2E; border:1px solid rgba(0,0,0,0.1); border-radius:8px; font-weight:600; text-decoration:none; text-align:center; cursor:pointer; box-sizing:border-box; line-height:1.4;">' + esc(product.secondary_cta_text) + '</a>\n';
    }
    
    // Bulk / contact note
    if (product.bulk_note) {
      html += '      <div class="ent-price-alt" style="margin-top:16px; font-size:0.85rem; color:#888; text-align:center;">\n';
      html += '        ' + product.bulk_note + '\n';
      html += '      </div>\n';
    }
    
    // Founders' Circle note
    if (product.founders_circle) {
      html += '      <p style="margin-top:12px; font-size:0.8rem; color:#888; text-align:center;">First 10 organizations qualify for Founders\' Circle — 50% cashback after 12 months.</p>\n';
    }
    
    html += '    </div>';
    
    return html;
  }

  // -- Main Render Function --
  function renderAll() {
    var containers = document.querySelectorAll('[data-mj-render]');
    
    for (var c = 0; c < containers.length; c++) {
      var container = containers[c];
      var mode = container.getAttribute('data-mj-render');
      var filter = container.getAttribute('data-mj-filter');
      var exclude = container.getAttribute('data-mj-exclude');
      
      var productsToRender = PRODUCTS;
      
      // Apply filter
      if (filter) {
        var filterIds = filter.split(',').map(function(s) { return s.trim(); });
        productsToRender = productsToRender.filter(function(p) {
          return filterIds.indexOf(p.id) !== -1;
        });
      }
      
      // Apply exclude
      if (exclude) {
        var excludeIds = exclude.split(',').map(function(s) { return s.trim(); });
        productsToRender = productsToRender.filter(function(p) {
          return excludeIds.indexOf(p.id) === -1;
        });
      }
      
      var html = '';
      
      switch (mode) {
        case 'pricing':
          productsToRender.sort(function(a, b) { return (a.tier || 99) - (b.tier || 99); });
          for (var i = 0; i < productsToRender.length; i++) {
            html += renderPricingCard(productsToRender[i]) + '\n';
          }
          break;
          
        case 'pricing-compact':
          productsToRender.sort(function(a, b) { return (a.tier || 99) - (b.tier || 99); });
          for (var j = 0; j < productsToRender.length; j++) {
            html += renderPricingCompactCard(productsToRender[j]) + '\n';
          }
          break;
          
        case 'coach-pro':
          productsToRender = productsToRender.filter(function(p) { return p.id === 'coach_pro'; });
          for (var k = 0; k < productsToRender.length; k++) {
            html += renderCoachProCard(productsToRender[k]);
          }
          break;
          
        case 'org-mirror':
          productsToRender = productsToRender.filter(function(p) { return p.id === 'org_mirror'; });
          for (var m = 0; m < productsToRender.length; m++) {
            html += renderOrgMirrorCard(productsToRender[m]);
          }
          break;
          
        default:
          console.warn('[MOJOWAY] Unknown render mode: ' + mode);
          continue;
      }
      
      container.innerHTML = html;
      console.log('[MOJOWAY] Rendered ' + mode + ': ' + productsToRender.length + ' card(s)');
    }
  }

  // -- Initialization --
  // v1.2: benefit fold toggle (called from an inline onclick)
  window.toggleMjFeatures = function(cardId, btnId) {
    var el = document.getElementById(cardId);
    var btn = document.getElementById(btnId);
    if (!el || !btn) return;
    var hidden = el.style.display === 'none';
    el.style.display = hidden ? 'block' : 'none';
    btn.innerHTML = hidden ? 'Hide details &uarr;' : 'Full details &darr;';
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderAll);
  } else {
    renderAll();
  }

  // -- Public API --
  window.MOJOWAY_RENDERER = {
    renderAll: renderAll,
    getProduct: getProduct,
    getProductByName: getProductByName
  };

  console.log('[MOJOWAY] Product renderer v1.1 ready (inline-styled buttons) — ' + PRODUCTS.length + ' products loaded (v' + (window.MOJOWAY_PRODUCTS_VERSION || '?') + ')');
})();
