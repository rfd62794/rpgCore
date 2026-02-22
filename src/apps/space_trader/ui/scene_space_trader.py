import sys
import pygame
from src.shared.engine.scene_manager import Scene
from src.shared.ui.panel import Panel
from src.shared.ui.label import Label
from src.shared.ui.button import Button
from src.shared.ui.scroll_list import ScrollList

from src.apps.space_trader.session import SpaceTraderSession
from src.apps.space_trader.ui.hud import SpaceTraderHUD

class SpaceTraderScene(Scene):
    """Main UI scene orchestrating the visual Space Trader loop."""
    
    def __init__(self, manager, session: SpaceTraderSession, **kwargs):
        super().__init__(manager, **kwargs)
        self.session = session
        
        self.width = self.manager.width
        self.height = self.manager.height
        
        self.hud = SpaceTraderHUD(session, self.width)
        
        # Core Colors
        self.bg_color = (10, 12, 16)
        self.panel_bg = (20, 25, 35)
        self.text_color = (220, 230, 240)
        
        # Message Log / Event feedback
        self.last_message = "Welcome to the frontier."
        
        self._build_ui()

    def on_enter(self, **kwargs) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _build_ui(self):
        """Constructs the panels and buttons based on current state."""
        self.panels = []
        self.buttons = []
        
        y_offset = self.hud.height + 20
        
        # 1. Location Panel (Top Left)
        loc_panel = Panel(20, y_offset, 400, 150, self.panel_bg)
        loc = self.session.graph.get(self.session.ship.location_id)
        loc_panel.add_element(Label(f"Location: {loc.name}", 15, 15, self.text_color))
        loc_panel.add_element(Label(f"Desc: {loc.description}", 15, 45, self.text_color))
        loc_panel.add_element(Label(f"Msg: {self.last_message}", 15, 100, (255, 200, 100)))
        self.panels.append(loc_panel)
        
        # 2. Ship Inventory (Top Right)
        inv_panel = Panel(self.width - 320, y_offset, 300, 300, self.panel_bg)
        inv_panel.add_element(Label("Cargo Manifest:", 15, 15, self.text_color))
        cy = 45
        for item, qty in self.session.ship.cargo.contents.items():
            inv_panel.add_element(Label(f"- {qty}x {item.title()}", 25, cy, self.text_color))
            cy += 30
        self.panels.append(inv_panel)
        
        # 3. Market List (Center Left)
        market_rect = pygame.Rect(20, y_offset + 170, 600, 300)
        self.market_list = ScrollList(market_rect, self.panel_bg)
        
        listings = self.session.market.get_listings(self.session.ship.location_id)
        for l in listings:
            good = l['good']
            row_text = f"{good.title():<15} | Buy: {l['buy_price']:<5} | Sell: {l['sell_price']:<5}"
            self.market_list.add_item(row_text, value=good)
            
        # Buy/Sell buttons for market
        bx = 640
        by = y_offset + 170
        btn_buy = Button(bx, by, 100, 40, "Buy 1", self._handle_buy)
        btn_sell = Button(bx, by + 50, 100, 40, "Sell 1", self._handle_sell)
        self.buttons.extend([btn_buy, btn_sell])
        
        # 4. Navigation Panel (Bottom)
        nav_y = self.height - 150
        nav_panel = Panel(20, nav_y, self.width - 40, 130, self.panel_bg)
        nav_panel.add_element(Label("Navigation Computer - Select Destination:", 15, 15, self.text_color))
        self.panels.append(nav_panel)
        
        neighbors = self.session.graph.neighbors(self.session.ship.location_id)
        nx = 40
        for n in neighbors:
            risk = self.session.get_risk_level(n.id)
            btn_text = f"{n.name} [{risk}]"
            btn = Button(nx, nav_y + 50, 240, 50, btn_text, lambda tgt=n.id: self._handle_travel(tgt))
            self.buttons.append(btn)
            nx += 260

    def _handle_buy(self):
        selected = self.market_list.get_selected_value()
        if selected:
            res = self.session.market.buy(self.session.ship.location_id, selected, 1, self.session.ship.cargo, self.session.ship.credits)
            self.session.ship.credits = res["credits"]
            self.last_message = res["message"]
            self._build_ui()

    def _handle_sell(self):
        selected = self.market_list.get_selected_value()
        if selected:
            res = self.session.market.sell(self.session.ship.location_id, selected, 1, self.session.ship.cargo, self.session.ship.credits)
            self.session.ship.credits = res["credits"]
            self.last_message = res["message"]
            self._build_ui()

    def _handle_travel(self, target_id: str):
        res = self.session.ship.travel(target_id, self.session.graph, self.session.encounter_system)
        self.last_message = res["message"]
        if res.get("encounter"):
            self.last_message = "ALERT: " + res["encounter"]["message"]
            
        self.session.price_model.update_daily()
        self._build_ui()

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.QUIT:
                self.request_quit()
                
            self.market_list.handle_event(event)
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt_ms: float) -> None:
        pass

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(self.bg_color)
        
        self.hud.draw(surface)
        
        for p in self.panels:
            p.draw(surface)
            
        self.market_list.draw(surface)
        
        for btn in self.buttons:
            btn.draw(surface)
