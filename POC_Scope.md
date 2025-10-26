# Flat Finder POC - Proof of Concept Scope

## Objective
Validate that automated apartment application submission is technically feasible and legally compliant for ImmobilienScout24.

## Success Criteria
- [ ] Successfully scrape new listings from ImmobilienScout24
- [ ] Generate a German rental application automatically
- [ ] Submit application through ImmobilienScout24's system
- [ ] Receive confirmation of successful submission
- [ ] Complete end-to-end flow within 10 minutes of listing publication

## POC Scope (2-3 weeks)

### Phase 1: Data Collection (Week 1)
**Goal**: Understand ImmobilienScout24's structure and submission process

#### Technical Tasks
- [ ] Analyze ImmobilienScout24 HTML structure and API endpoints
- [ ] Map application submission flow (forms, required fields, validation)
- [ ] Document anti-bot measures (rate limits, CAPTCHAs, detection methods)
- [ ] Test different scraping approaches (requests, selenium, playwright)

#### Deliverables
- Technical analysis document
- Working scraper that extracts listing details
- Application form field mapping

### Phase 2: Application Generation (Week 2)
**Goal**: Create basic German rental application

#### Technical Tasks
- [ ] Build simple German cover letter template
- [ ] Create PDF generation for application documents
- [ ] Implement basic form data population
- [ ] Test document formatting and completeness

#### Deliverables
- German application template (basic)
- PDF generation pipeline
- Sample generated applications

### Phase 3: Automated Submission (Week 3)
**Goal**: Complete end-to-end automation

#### Technical Tasks
- [ ] Implement automated form submission
- [ ] Handle authentication and session management
- [ ] Add error handling and retry logic
- [ ] Test submission confirmation detection

#### Deliverables
- Working end-to-end automation
- Error handling documentation
- Success/failure metrics

## Technical Stack (Minimal)

### Backend
- **Language**: Python (rapid prototyping)
- **Web Scraping**: BeautifulSoup + Requests or Selenium
- **State & Storage**: Supabase Postgres (via Supabase Python client) + Redis (optional caching)
- **Identity**: Supabase Auth for multi-tenant user management
- **PDF Generation**: ReportLab or WeasyPrint
- **Scheduling**: Basic cron or Python scheduler

### Frontend
- **Framework**: Next.js (TypeScript) deployed with Supabase auth UI
- **UI Components**: Tailwind CSS + Headless UI
- **State Management**: React Query for Supabase data
- **Purpose**: Registration, preference questionnaire, application status dashboard

## Out of Scope for POC

### Features NOT Included
- ❌ Multiple platforms (only ImmobilienScout24)
- ❌ Advanced AI cover letter generation
- ❌ Real-time WebSocket monitoring
- ❌ User dashboard or web interface
- ❌ Advanced analytics or CRM features
- ❌ GDPR compliance infrastructure
- ❌ Production-grade security measures
- ❌ Scalable infrastructure

### Assumptions for POC
- Manual user document upload
- Single test user profile
- Basic German template (no personalization)
- Development environment only
- Manual monitoring of results

## Risk Assessment

### High Risk
- **Platform blocking**: ImmobilienScout24 may detect and block automation
- **Legal issues**: Potential ToS violations
- **Technical complexity**: Hidden anti-bot measures

### Medium Risk
- **Application quality**: Generated applications may be rejected
- **Rate limiting**: May need to slow down scraping significantly
- **Form changes**: Platform may update forms frequently

### Mitigation Strategies
- **Respectful scraping**: Conservative rate limits, mimic human behavior
- **Legal review**: Consult legal expert before POC completion
- **Gradual testing**: Start with manual steps, automate incrementally

## Data Requirements

### Minimum User Data
- Name, email, phone
- Current address
- Employment information
- Monthly income
- Basic preferences (price range, location, size)

### Test Listings Criteria
- Price: €800-1500/month
- Location: Berlin (specific districts TBD)
- Size: 1-2 rooms
- Recently posted (within 1 hour)

## POC Validation Metrics

### Technical Metrics
- **Scraping success rate**: >90% of listings extracted correctly
- **Submission success rate**: >80% of submissions complete without errors
- **Speed**: <5 minutes from listing detection to submission
- **Reliability**: POC runs successfully 3 out of 5 test attempts

### Business Metrics
- **Application quality**: Generated applications include all required information
- **Response rate**: At least 1 response from 10 submitted applications
- **Platform compliance**: No blocking or account suspension during testing

## Next Steps After POC

### If Successful
- Expand to additional platforms (WG-gesucht, Facebook)
- Implement production-grade infrastructure
- Add AI-powered personalization
- Build user interface and CRM features

### If Partially Successful
- Identify and address specific technical challenges
- Modify approach based on learnings
- Consider hybrid manual/automated model

### If Unsuccessful
- Pivot to manual application assistance service
- Focus on document generation only
- Explore partnership opportunities with existing platforms

## Timeline

### Week 1: Analysis & Basic Scraping
- Days 1-2: Platform analysis and documentation
- Days 3-5: Build and test basic scraper
- Days 4-5: Bootstrap Supabase project (auth, `users`, `preferences`, `listings` tables) and connect Python backend

### Week 2: Application Generation
- Days 1-2: Template creation and PDF generation
- Days 2-3: Integrate Supabase preference reads into matching pipeline
- Days 3-5: Build Next.js onboarding flow (Supabase auth + preference questionnaire)
- Days 4-5: Integration testing and refinement

### Week 3: Automation & Testing
- Days 1-2: Submission automation
- Days 2-3: End-to-end pipeline storing applications in Supabase (`applications`, `application_events`)
- Days 4-5: Frontend dashboard listing applications with statuses + documentation

## Resources Needed
- 1 developer (full-time for 3 weeks)
- ImmobilienScout24 test account
- Sample documents for testing
- Legal consultation (2-3 hours)
- Berlin apartment listings for testing

## Real-Time Monitoring Technical Solution

### Overview
**Multi-User SaaS Architecture**: Centralized monitoring system that tracks ALL new apartment listings on ImmobilienScout24, then matches them against individual user preferences and criteria in real-time.

### SaaS Architecture Design

#### System Flow
1. **Global Monitoring** → Monitor ALL new listings on ImmobilienScout24
2. **Preference Matching** → Check each new listing against all user preferences
3. **User Notification** → Alert users when listings match their criteria
4. **Application Triggering** → Automatically apply for matched listings (per user settings)

```python
# High-level system flow
async def process_new_listing(listing):
    # 1. Store listing in database
    await store_listing(listing)
    
    # 2. Find matching users
    matching_users = await find_matching_users(listing)
    
    # 3. Process each match
    for user in matching_users:
        await notify_user(user, listing)
        if user.auto_apply_enabled:
            await trigger_application(user, listing)
```

### Multi-Tenant Monitoring Architecture

#### Core Components

**1. Global Listing Monitor**
```python
class GlobalListingMonitor:
    """Monitors ALL listings for all users"""
    
    def __init__(self):
        self.session = requests.Session()
        self.seen_listings = set()
        # Monitor comprehensive search (no filters)
        self.monitoring_urls = [
            "https://www.immobilienscout24.de/Suche/de/berlin/berlin/wohnung-mieten",
            "https://www.immobilienscout24.de/api/search/v1/search?city=berlin&type=rent"
        ]
    
    async def start_global_monitoring(self):
        """Monitor all listings without user-specific filters"""
        while True:
            try:
                new_listings = await self.scan_for_new_listings()
                if new_listings:
                    await self.process_new_listings(new_listings)
                
                await asyncio.sleep(self.get_poll_interval())
            except Exception as e:
                await self.handle_monitoring_error(e)
    
    async def process_new_listings(self, listings):
        """Process each new listing against all user preferences"""
        for listing in listings:
            # Store listing globally
            await self.store_listing(listing)
            
            # Find matching users asynchronously
            asyncio.create_task(self.match_against_users(listing))
```

**2. User Preference Engine**
```python
class UserPreferenceEngine:
    """Matches listings against user criteria"""
    
    def __init__(self):
        self.db = Database()
        self.cache = Redis()
    
    async def find_matching_users(self, listing):
        """Find all users whose preferences match this listing"""
        
        # Get all active user preferences (cached)
        user_preferences = await self.get_active_user_preferences()
        
        matching_users = []
        for user_id, preferences in user_preferences.items():
            if self.listing_matches_preferences(listing, preferences):
                matching_users.append({
                    'user_id': user_id,
                    'preferences': preferences,
                    'match_score': self.calculate_match_score(listing, preferences)
                })
        
        return matching_users
    
    def listing_matches_preferences(self, listing, preferences):
        """Check if listing matches user preferences"""
        
        # Price range check
        if not self.price_in_range(listing.price, preferences.price_min, preferences.price_max):
            return False
        
        # Location check
        if not self.location_matches(listing.location, preferences.preferred_districts):
            return False
        
        # Size requirements
        if not self.size_matches(listing.rooms, listing.size_sqm, preferences):
            return False
        
        # Additional filters (pets, balcony, etc.)
        if not self.additional_criteria_match(listing, preferences):
            return False
        
        return True
    
    def calculate_match_score(self, listing, preferences):
        """Calculate how well listing matches user preferences (0-100)"""
        score = 0
        
        # Price preference (closer to ideal = higher score)
        if preferences.ideal_price:
            price_diff = abs(listing.price - preferences.ideal_price)
            price_score = max(0, 100 - (price_diff / preferences.ideal_price * 100))
            score += price_score * 0.3
        
        # Location preference
        if listing.district in preferences.top_preferred_districts:
            score += 30
        elif listing.district in preferences.acceptable_districts:
            score += 15
        
        # Size preference
        if preferences.ideal_rooms and listing.rooms == preferences.ideal_rooms:
            score += 20
        
        # Additional amenities
        amenity_matches = self.count_amenity_matches(listing, preferences)
        score += amenity_matches * 5
        
        return min(100, score)
```

**3. User Management System**
```python
class UserManager:
    """Manages user preferences and settings"""
    
    async def create_user_preference(self, user_id, preferences):
        """Create or update user search preferences"""
        
        preference_data = {
            'user_id': user_id,
            'price_min': preferences.price_min,
            'price_max': preferences.price_max,
            'ideal_price': preferences.ideal_price,
            'preferred_districts': preferences.districts,
            'min_rooms': preferences.min_rooms,
            'max_rooms': preferences.max_rooms,
            'min_size_sqm': preferences.min_size_sqm,
            'pet_friendly': preferences.pet_friendly,
            'balcony_required': preferences.balcony_required,
            'furnished': preferences.furnished,
            'auto_apply': preferences.auto_apply_enabled,
            'notification_methods': preferences.notification_methods,
            'is_active': True,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        await self.db.upsert_user_preferences(preference_data)
        
        # Update cache for real-time matching
        await self.cache_user_preferences(user_id, preference_data)
    
    async def get_active_user_preferences(self):
        """Get all active user preferences for matching"""
        
        # Try cache first
        cached_prefs = await self.cache.get('active_user_preferences')
        if cached_prefs:
            return json.loads(cached_prefs)
        
        # Fallback to database
        prefs = await self.db.get_active_user_preferences()
        
        # Cache for 5 minutes
        await self.cache.setex('active_user_preferences', 300, json.dumps(prefs))
        
        return prefs
```

**4. Notification & Application System**
```python
class UserNotificationSystem:
    """Handles user notifications and automated applications"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.push_service = PushNotificationService()
        self.application_service = ApplicationService()
    
    async def notify_user_of_match(self, user_id, listing, match_score):
        """Notify user of matching listing"""
        
        user = await self.get_user(user_id)
        
        # Send notifications based on user preferences
        notification_tasks = []
        
        if 'email' in user.notification_methods:
            notification_tasks.append(
                self.send_email_notification(user, listing, match_score)
            )
        
        if 'push' in user.notification_methods:
            notification_tasks.append(
                self.send_push_notification(user, listing, match_score)
            )
        
        if 'sms' in user.notification_methods and match_score > 80:
            notification_tasks.append(
                self.send_sms_notification(user, listing, match_score)
            )
        
        # Send all notifications concurrently
        await asyncio.gather(*notification_tasks)
        
        # Trigger auto-application if enabled
        if user.auto_apply_enabled and match_score >= user.auto_apply_threshold:
            await self.trigger_auto_application(user, listing)
    
    async def trigger_auto_application(self, user, listing):
        """Automatically apply for listing on behalf of user"""
        
        application_data = {
            'user_id': user.id,
            'listing_id': listing.id,
            'listing_url': listing.url,
            'application_type': 'automated',
            'match_score': listing.match_score,
            'triggered_at': datetime.now()
        }
        
        # Queue application for processing
        await self.application_service.queue_application(application_data)
```

### Database Schema for Multi-User System

#### Global Listings Table
```sql
create table if not exists listings (
    id bigint generated always as identity primary key,
    external_id text unique not null,
    title text not null,
    price integer not null,
    deposit integer,
    district varchar(100),
    address text,
    rooms decimal(2,1),
    size_sqm integer,
    available_from date,
    pet_friendly boolean default false,
    balcony boolean default false,
    furnished boolean default null,  -- null = no preference
    listing_url text not null,
    raw_data jsonb,  -- Store full scraped data
    first_seen_at timestamp default now(),
    is_active boolean default true
);
alter table listings enable row level security;
```

#### User Preferences Table
```sql
create table if not exists user_preferences (
    id bigint generated always as identity primary key,
    user_id bigint not null,
    price_min integer,
    price_max integer,
    ideal_price integer,
    preferred_districts jsonb,  -- ["Mitte", "Prenzlauer Berg", ...]
    min_rooms integer,
    max_rooms integer,
    min_size_sqm integer,
    pet_friendly boolean default false,
    balcony_required boolean default false,
    furnished boolean default null,  -- null = no preference
    auto_apply boolean default false,
    auto_apply_threshold integer default 80,  -- match score threshold
    notification_methods jsonb default '["email"]',
    is_active boolean default true,
    created_at timestamp default now(),
    updated_at timestamp default now()
);
alter table user_preferences enable row level security;
```

#### User Matches Table
```sql
create table if not exists user_matches (
    id bigint generated always as identity primary key,
    user_id bigint not null,
    listing_id bigint not null,
    match_score integer not null,
    notified_at timestamp default now(),
    application_triggered boolean default false,
    application_sent_at timestamp,
    UNIQUE(user_id, listing_id)
);
alter table user_matches enable row level security;
```

### Performance Optimizations for Multi-User System

#### 1. Efficient Preference Matching
```python
class OptimizedMatcher:
    """Optimized matching for large number of users"""
    
    def __init__(self):
        self.price_index = defaultdict(list)  # price_range -> [user_ids]
        self.district_index = defaultdict(list)  # district -> [user_ids]
        self.rebuild_indexes_interval = 300  # 5 minutes
    
    async def build_user_indexes(self):
        """Build indexes for fast matching"""
        users = await self.get_active_users()
        
        self.price_index.clear()
        self.district_index.clear()
        
        for user in users:
            # Index by price ranges
            price_key = f"{user.price_min}-{user.price_max}"
            self.price_index[price_key].append(user.id)
            
            # Index by districts
            for district in user.preferred_districts:
                self.district_index[district].append(user.id)
    
    def get_candidate_users(self, listing):
        """Get users who might match based on price/location indexes"""
        candidate_users = set()
        
        # Find users by price range
        for price_range, user_ids in self.price_index.items():
            min_price, max_price = map(int, price_range.split('-'))
            if min_price <= listing.price <= max_price:
                candidate_users.update(user_ids)
        
        # Find users by district
        if listing.district in self.district_index:
            candidate_users.update(self.district_index[listing.district])
        
        return list(candidate_users)
```

#### 2. Caching Strategy
```python
class MatchingCache:
    """Cache frequently used data for matching"""
    
    def __init__(self):
        self.redis = Redis()
        self.user_prefs_cache_ttl = 300  # 5 minutes
        self.listing_cache_ttl = 3600   # 1 hour
    
    async def cache_user_preferences(self):
        """Cache all active user preferences"""
        users = await self.db.get_active_user_preferences()
        
        # Cache individual user preferences
        for user in users:
            key = f"user_prefs:{user.id}"
            await self.redis.setex(key, self.user_prefs_cache_ttl, json.dumps(user))
        
        # Cache aggregated preferences for quick lookup
        aggregated = self.aggregate_preferences(users)
        await self.redis.setex("aggregated_prefs", self.user_prefs_cache_ttl, json.dumps(aggregated))
```

### Monitoring & Analytics for SaaS

#### System Metrics
```python
SAAS_METRICS = {
    'total_active_users': 0,
    'total_listings_processed_today': 0,
    'average_matches_per_listing': 0,
    'successful_applications_today': 0,
    'notification_delivery_rate': 0,
    'system_processing_latency': 0,  # time from listing detection to user notification
}
```

#### User Analytics
```python
async def track_user_engagement(self, user_id, event_type, event_data):
    """Track user engagement for product improvement"""
    
    analytics_event = {
        'user_id': user_id,
        'event_type': event_type,  # 'match_received', 'application_sent', 'preferences_updated'
        'event_data': event_data,
        'timestamp': datetime.now()
    }
    
    await self.analytics_db.insert_event(analytics_event)
```

### Implementation Priority for SaaS POC
#### Week 1 Focus (POC)
1. Global monitor storing listings in Supabase
2. Supabase schema + auth configuration
3. Next.js auth scaffolding with Supabase
4. Simple change detection using Supabase tables

#### Week 2 Focus
1. Preference matching against Supabase data
2. Notification pipeline using Supabase functions / edge workers
3. User dashboard (Next.js) showing matches and application history
4. Match scoring + auto-apply toggles persisted in Supabase

#### Week 3 Focus
1. Performance optimization (caching, indexing)
2. Auto-application integration
3. Multi-user testing with different preferences
4. Analytics and monitoring
