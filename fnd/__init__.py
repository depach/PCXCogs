from .flashndash import FlashNDash


async def setup(bot):
    await bot.add_cog(FlashNDash(bot))
