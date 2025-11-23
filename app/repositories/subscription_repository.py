from sqlalchemy.ext.asyncio import AsyncSession


class SubscriptionRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    
        