# parts and ordering

quotes and availability checked October 11, 2026. these are for one assembled board, with five bare PCBs because that is the quoted batch. supplier minimum quantities mean some spare components are included. no purchases made yet

there are 414 fitted components across 110 part numbers. [parts-one-board.csv](parts-one-board.csv) lists the fitted quantities; [purchasing-draft.csv](purchasing-draft.csv) adds order quantities, exact order codes, prices and sources. the root [bom.csv](../bom.csv) also includes DNP parts

## quotes

| Supplier | Contents | Merchandise | Shipping and adjustments | Quoted total |
| --- | --- | ---: | --- | ---: |
| PCBWay | five four-layer boards and one top stencil | $321.90 | $28.95 DHL, minus $6.44 member discount | $344.41 |
| LCSC | 85 in-stock part lines | $123.48 | $13.88 shipping, minus $1.55 merchandise and $12 shipping discounts | $123.81 |
| Mouser | 14 in-stock lines and the backordered brake shunt | $28.54 | $8.49 UPS Ground and $2.33 estimated tariff | $39.36 |
| Coilcraft | one MSS1246T-683MLC | $2.41 | $0.58 tariff surcharge; shipping still TBD | $2.99 before shipping |

these cart totals are separate quotes, not a complete order total. the MCU partner offer, other backordered lines and XT60 reference price below are not all in those carts. sales tax and any additional import costs are not finalized

PCBWay's bare-board quote is $311.90 and the stencil is $10. the $10 coupon found in the account is available but has not been applied, so it is not subtracted here. the earlier $131.63 PCB quote used 1 oz outer copper and does not apply to this board

all 110 component lines below add up to $191.29 in merchandise, including the backorders and unconfirmed offers. adding the $311.90 PCB batch and $10 stencil gives $513.19 before shipping, tax and discounts. do not add that figure to the cart totals above

## website BOM

Half Life has 45 grouped rows covering the boards and components. its parts subtotal is $501.69 and its shipping/tariff field is $42.23, for $543.92. the website rounds unit prices to cents and includes the $1.55 LCSC merchandise discount. the assembly stencil is separate from its parts-only list

the $42.23 allowance is $28.95 PCBWay shipping + $1.88 LCSC shipping after the coupon + $8.49 Mouser shipping + $2.33 Mouser tariff estimate + $0.58 Coilcraft surcharge. it does not include final sales tax, additional duties, Coilcraft shipping or a US shipping quote for the XT60. the PCBWay member discount is not subtracted in the website list

four supplier cart screenshots are attached to the submission form. the repo checks pass, but the form still disables Next on the tier screen. submission is paused while that is sorted out

## still to source

100 part numbers had confirmed stock at LCSC, Mouser or Coilcraft when checked. these ten need more work:

| Part | Fitted qty | Status |
| --- | ---: | --- |
| BM02B-GHS-TBT(LF)(SN) | 2 | backordered; delivery not confirmed |
| BM05B-GHS-TBT(LF)(SN) | 2 | backordered; delivery not confirmed |
| INA241A2IDR | 3 | backordered; delivery not confirmed |
| RC0603FR-07301KL | 1 | backordered; delivery not confirmed |
| STM32G474VET6 | 1 | cart marks backordered; partner advertises 3 units and 7-9 business days; confirmation required |
| TCAN3403DRQ1 | 1 | backordered; delivery not confirmed |
| TLV9024PWR | 2 | backordered; delivery not confirmed |
| TPS3431SDRBR | 1 | backordered; delivery not confirmed |
| WSLP25123L000FEA | 1 | backordered; delivery not confirmed |
| XT60PW-M | 1 | international listing 726 in stock; US storefront error; US quote not confirmed |

the MCU offer is kept in a separate LCSC cart, `BLDC ESC - confirm stock`. its partner listing advertises a small quantity, but the cart marks it backordered. that is not confirmed inventory

two order codes were corrected without changing the circuit or footprints: R310 is `WSLP25123L000FEA`, and D703 is `PESD2CANFD24V-TR`. the Nexperia diode is now in the LCSC cart. the brake shunt is still backordered at Mouser

## board and stencil

PCBWay is reviewing a 116 x 112 mm, four-layer, 1.6 mm board with 2 oz outer and 1 oz inner copper. minimum inner logic routing is 0.127 mm; outer routing is 0.200 mm. vias are 0.20 mm drill / 0.50 mm pad. the quote form forces 8 mil globally, so the actual layer-specific geometry is in the uploaded notes

the bottom USB pair targets 90 ohms differential, with 0.228 mm tracks, a 0.200 mm pair gap and 0.250 mm coplanar ground gap, referenced to In2.Cu. the actual stack and impedance still need PCBWay's approval. a price review has been requested too

the top stencil is frameless, 190 x 290 mm, 0.10 mm thick. C215, C235, C255, R103, R217, R237 and R257 have no paste apertures because they are DNP. thermal pads keep their segmented apertures. final aperture review is pending

## complete component list

Fitted is the quantity on one board. Order includes supplier minimum quantities. prices below are the saved quotes, not a claim that every part can ship now

| Part | Manufacturer | Fitted | Order | Vendor / part | Unit USD | Line USD | Availability |
| --- | --- | ---: | ---: | --- | ---: | ---: | --- |
| 1711725 | Phoenix Contact | 1 | 1 | [LCSC C89120](https://www.lcsc.com/product-detail/C89120.html) | 1.10 | 1.10 | in stock |
| 2N7002P,215 | Nexperia | 1 | 20 | [LCSC C81488](https://www.lcsc.com/product-detail/C81488.html) | 0.0246 | 0.49 | in stock |
| ABM3-8.000MHZ-D2Y-T | Abracon | 1 | 1 | [LCSC C144380](https://www.lcsc.com/product-detail/C144380.html) | 0.5656 | 0.57 | in stock |
| BAT54H,115 | Nexperia | 2 | 5 | [LCSC C426769](https://www.lcsc.com/product-detail/C426769.html) | 0.1452 | 0.73 | in stock |
| BAV199,215 | Nexperia | 8 | 10 | [LCSC C40919](https://www.lcsc.com/product-detail/C40919.html) | 0.0429 | 0.43 | in stock |
| BLM18KG601SN1D | Murata | 1 | 50 | [LCSC C85833](https://www.lcsc.com/product-detail/C85833.html) | 0.018 | 0.90 | in stock |
| BM02B-GHS-TBT(LF)(SN) | JST | 2 | 2 | [Mouser 306-BM02BGHSTBTLFSNN](https://www.mouser.com/en/ProductDetail/JST/BM02B-GHS-TBTLFSN?qs=cdbOS8ANM9BvfZxSeyCAhA%3D%3D) | 0.32 | 0.64 | backordered; delivery not confirmed |
| BM03B-GHS-TBT(LF)(SN) | JST | 5 | 5 | [LCSC C161691](https://www.lcsc.com/product-detail/C161691.html) | 0.3825 | 1.91 | in stock |
| BM04B-GHS-TBT(LF)(SN) | JST | 1 | 5 | [LCSC C161692](https://www.lcsc.com/product-detail/C161692.html) | 0.3962 | 1.98 | in stock |
| BM05B-GHS-TBT(LF)(SN) | JST | 2 | 2 | [Mouser 306-BM05BGHSTBTLFSNN](https://www.mouser.com/en/ProductDetail/JST/BM05B-GHS-TBTLFSN?qs=cdbOS8ANM9B3tGFuHaxqMA%3D%3D) | 0.48 | 0.96 | backordered; delivery not confirmed |
| C0603C101J5GACTU | KEMET | 7 | 50 | [LCSC C2167328](https://www.lcsc.com/product-detail/C2167328.html) | 0.0252 | 1.26 | in stock |
| C0603C102J5GACTU | KEMET | 19 | 20 | [LCSC C2181873](https://www.lcsc.com/product-detail/C2181873.html) | 0.0267 | 0.53 | in stock |
| C0603C103K5RACTU | KEMET | 13 | 13 | [Mouser 80-C0603C103K5R](https://www.mouser.com/en/ProductDetail/KEMET/C0603C103K5RACTU?qs=aZBT8IJKz4hu1X55tMAU6Q%3D%3D) | 0.068 | 0.88 | in stock |
| C0603C104K1RACTU | KEMET | 1 | 1 | [Mouser 80-C0603C104K1RACTU](https://www.mouser.com/en/ProductDetail/KEMET/C0603C104K1RACTU?qs=ulEaXIWI0c%252BGZAOcX%252BBs5A%3D%3D) | 0.59 | 0.59 | in stock |
| C0603C104K5RACTU | KEMET | 48 | 50 | [LCSC C127833](https://www.lcsc.com/product-detail/C127833.html) | 0.0449 | 2.25 | in stock |
| C0603C105K4RACTU | KEMET | 10 | 20 | [LCSC C2167386](https://www.lcsc.com/product-detail/C2167386.html) | 0.0423 | 0.85 | in stock |
| C0603C221J5GACTU | KEMET | 4 | 20 | [LCSC C452747](https://www.lcsc.com/product-detail/C452747.html) | 0.0228 | 0.46 | in stock |
| C0603C222J5GACTU | KEMET | 2 | 20 | [LCSC C2167437](https://www.lcsc.com/product-detail/C2167437.html) | 0.0387 | 0.77 | in stock |
| C0603C270J5GACTU | KEMET | 2 | 2 | [Mouser 80-C0603C270J5G](https://www.mouser.com/en/ProductDetail/KEMET/C0603C270J5GACTU?qs=tmo4rc6ZD9Wc1Km2xObD4A%3D%3D) | 0.10 | 0.20 | in stock |
| C0603C473K5RACTU | KEMET | 1 | 20 | [LCSC C3019600](https://www.lcsc.com/product-detail/C3019600.html) | 0.0122 | 0.24 | in stock |
| C0603C820J5GACTU | KEMET | 1 | 50 | [LCSC C2169253](https://www.lcsc.com/product-detail/C2169253.html) | 0.0159 | 0.80 | in stock |
| C0805C105K3RACTU | KEMET | 1 | 10 | [LCSC C2167365](https://www.lcsc.com/product-detail/C2167365.html) | 0.068 | 0.68 | in stock |
| C0805C473K1RACTU | KEMET | 1 | 10 | [LCSC C2174835](https://www.lcsc.com/product-detail/C2174835.html) | 0.0394 | 0.39 | in stock |
| C0805C475K3RACTU | KEMET | 4 | 5 | [LCSC C22409262](https://www.lcsc.com/product-detail/C22409262.html) | 0.1956 | 0.98 | in stock |
| C1206C472KDRACTU | KEMET | 1 | 1 | [Mouser 80-C1206C472KDR](https://www.mouser.com/en/ProductDetail/KEMET/C1206C472KDRACTU?qs=4%252BoambldWwZLyeRVCG8sdw%3D%3D) | 0.51 | 0.51 | in stock |
| C3216X7R1H105K160AB | TDK | 1 | 1 | [Mouser 810-C3216X7R1H105K](https://www.mouser.com/en/ProductDetail/TDK/C3216X7R1H105K160AB?qs=NRhsANhppD9o2v7nR8CCQg%3D%3D) | 0.65 | 0.65 | in stock |
| C3216X7R2A105K160AA | TDK | 6 | 6 | [Mouser 810-C3216X7R2A105K](https://www.mouser.com/en/ProductDetail/TDK/C3216X7R2A105K160AA?qs=NRhsANhppD9a%252B8xqdqiZiQ%3D%3D) | 0.76 | 4.56 | in stock |
| CGA6N3X7R2A225K230AB | TDK | 2 | 2 | [Mouser 810-CGA6N3X7R2A225K](https://www.mouser.com/en/ProductDetail/TDK/CGA6N3X7R2A225K230AB?qs=NRhsANhppD8IGlRP%252BrSh7w%3D%3D) | 1.16 | 2.32 | in stock |
| CSS4J-4026R-1L00F | Bourns | 3 | 3 | [LCSC C2076400](https://www.lcsc.com/product-detail/C2076400.html) | 1.7049 | 5.11 | in stock |
| DRV8353SRTAT | Texas Instruments | 1 | 1 | [LCSC C2150480](https://www.lcsc.com/product-detail/C2150480.html) | 5.2998 | 5.30 | in stock |
| EEUFC1J220 | Panasonic | 1 | 1 | [Mouser 667-EEU-FC1J220](https://www.mouser.com/en/ProductDetail/Panasonic/EEU-FC1J220?qs=%2Fhqyh7o0k%2FVXxz3al1BEQA%3D%3D) | 0.46 | 0.46 | in stock |
| FTSH-105-01-L-DV-007-K | Samtec | 1 | 1 | [LCSC C5296739](https://www.lcsc.com/product-detail/C5296739.html) | 2.4278 | 2.43 | in stock |
| GXC1J101MCW1GS | Nichicon | 10 | 10 | [Mouser 647-GXC1J101MCW1GS](https://www.mouser.com/en/ProductDetail/Nichicon/GXC1J101MCW1GS?qs=VVKQmw408U%252B1tvMYj%252BHCdw%3D%3D) | 1.52 | 15.20 | in stock |
| INA180A1IDBVR | Texas Instruments | 1 | 5 | [LCSC C122228](https://www.lcsc.com/product-detail/C122228.html) | 0.2782 | 1.39 | in stock |
| INA241A2IDR | Texas Instruments | 3 | 3 | [Mouser 595-INA241A2IDR](https://www.mouser.com/en/ProductDetail/Texas-Instruments/INA241A2IDR?qs=ST9lo4GX8V2BJPaEYaZuzQ%3D%3D) | 3.45 | 10.35 | backordered; delivery not confirmed |
| ISC011N06LM5ATMA1 | Infineon | 7 | 7 | [LCSC C3288866](https://www.lcsc.com/product-detail/C3288866.html) | 4.5575 | 31.90 | in stock |
| LM5164DDAR | Texas Instruments | 1 | 1 | [LCSC C477928](https://www.lcsc.com/product-detail/C477928.html) | 1.9959 | 2.00 | in stock |
| LTST-C190KGKT | Lite-On | 3 | 50 | [LCSC C125094](https://www.lcsc.com/product-detail/C125094.html) | 0.0168 | 0.84 | in stock |
| M20-9990245 | Harwin | 4 | 5 | [LCSC C3338413](https://www.lcsc.com/product-detail/C3338413.html) | 0.1248 | 0.62 | in stock |
| M20-9990345 | Harwin | 1 | 5 | [LCSC C3337081](https://www.lcsc.com/product-detail/C3337081.html) | 0.2406 | 1.20 | in stock |
| M24C64-RMN6TP | STMicroelectronics | 1 | 5 | [LCSC C79988](https://www.lcsc.com/product-detail/C79988.html) | 0.151 | 0.76 | in stock |
| MF-PSMF050X-2 | Bourns | 1 | 20 | [LCSC C116170](https://www.lcsc.com/product-detail/C116170.html) | 0.0587 | 1.17 | in stock |
| MSAST32MSB7226KPNB25 | Taiyo Yuden | 2 | 5 | [LCSC C7235328](https://www.lcsc.com/product-detail/C7235328.html) | 0.3621 | 1.81 | in stock |
| MSS1246T-683MLC | Coilcraft | 1 | 1 | [Coilcraft MSS1246T-683MLC](https://www.coilcraft.com/en-us/products/power/shielded-inductors/ferrite-drum/mss-mos/mss1246t/mss1246t-683/) | 2.41 | 2.41 | 588 in stock; US warehouse; shipping not yet quoted |
| MT60-M | AMASS | 1 | 1 | [LCSC C99176](https://www.lcsc.com/product-detail/C99176.html) | 0.4992 | 0.50 | in stock |
| NCP18XH103F03RB | Murata | 2 | 10 | [LCSC C13564](https://www.lcsc.com/product-detail/C13564.html) | 0.0467 | 0.47 | in stock |
| PESD2CANFD24V-TR | Nexperia | 1 | 5 | [LCSC C552486](https://www.lcsc.com/product-detail/C552486.html) | 0.2691 | 1.35 | in stock; added after order-code correction |
| PESD5V0S1BA,115 | Nexperia | 14 | 15 | [LCSC C19224](https://www.lcsc.com/product-detail/C19224.html) | 0.0861 | 1.29 | in stock |
| PMEG2010ER,115 | Nexperia | 1 | 5 | [LCSC C82288](https://www.lcsc.com/product-detail/C82288.html) | 0.1833 | 0.92 | in stock |
| RC0603FR-07100KL | Yageo | 17 | 100 | [LCSC C14675](https://www.lcsc.com/product-detail/C14675.html) | 0.0026 | 0.26 | in stock |
| RC0603FR-07100RL | Yageo | 11 | 100 | [LCSC C105588](https://www.lcsc.com/product-detail/C105588.html) | 0.0024 | 0.24 | in stock |
| RC0603FR-0710KL | Yageo | 38 | 100 | [LCSC C98220](https://www.lcsc.com/product-detail/C98220.html) | 0.0034 | 0.34 | in stock |
| RC0603FR-0712K1L | Yageo | 2 | 100 | [LCSC C123417](https://www.lcsc.com/product-detail/C123417.html) | 0.0031 | 0.31 | in stock |
| RC0603FR-07150KL | Yageo | 2 | 100 | [LCSC C114660](https://www.lcsc.com/product-detail/C114660.html) | 0.0036 | 0.36 | in stock |
| RC0603FR-0715KL | Yageo | 1 | 100 | [LCSC C114661](https://www.lcsc.com/product-detail/C114661.html) | 0.0044 | 0.44 | in stock |
| RC0603FR-071KL | Yageo | 20 | 100 | [LCSC C22548](https://www.lcsc.com/product-detail/C22548.html) | 0.0037 | 0.37 | in stock |
| RC0603FR-071ML | Yageo | 1 | 100 | [LCSC C105578](https://www.lcsc.com/product-detail/C105578.html) | 0.0042 | 0.42 | in stock |
| RC0603FR-071RL | Yageo | 1 | 100 | [LCSC C112305](https://www.lcsc.com/product-detail/C112305.html) | 0.0063 | 0.63 | in stock |
| RC0603FR-07200KL | Yageo | 2 | 100 | [LCSC C105574](https://www.lcsc.com/product-detail/C105574.html) | 0.004 | 0.40 | in stock |
| RC0603FR-0722RL | Yageo | 2 | 100 | [LCSC C107701](https://www.lcsc.com/product-detail/C107701.html) | 0.0037 | 0.37 | in stock |
| RC0603FR-072M49L | Yageo | 1 | 1 | [Mouser 603-RC0603FR-072M49L](https://www.mouser.com/en/ProductDetail/YAGEO/RC0603FR-072M49L?qs=0yPvnVz5%2FmpCuPxzZx6xew%3D%3D) | 0.11 | 0.11 | in stock |
| RC0603FR-072R2L | Yageo | 1 | 100 | [LCSC C112307](https://www.lcsc.com/product-detail/C112307.html) | 0.0098 | 0.98 | in stock |
| RC0603FR-07300KL | Yageo | 2 | 100 | [LCSC C114667](https://www.lcsc.com/product-detail/C114667.html) | 0.0023 | 0.23 | in stock |
| RC0603FR-07301KL | Yageo | 1 | 1 | [Mouser 603-RC0603FR-07301KL](https://www.mouser.com/en/ProductDetail/YAGEO/RC0603FR-07301KL?qs=diQw95jMAeNJi3XO%2F%2FwC0g%3D%3D) | 0.10 | 0.10 | backordered; delivery not confirmed |
| RC0603FR-073R3L | Yageo | 6 | 100 | [LCSC C137725](https://www.lcsc.com/product-detail/C137725.html) | 0.0082 | 0.82 | in stock |
| RC0603FR-0742K2L | Yageo | 1 | 1 | [Mouser 603-RC0603FR-0742K2L](https://www.mouser.com/en/ProductDetail/YAGEO/RC0603FR-0742K2L?qs=gt6vzsuosg2g3L%2FVaGpSfQ%3D%3D) | 0.10 | 0.10 | in stock |
| RC0603FR-0747KL | Yageo | 7 | 100 | [LCSC C105579](https://www.lcsc.com/product-detail/C105579.html) | 0.0031 | 0.31 | in stock |
| RC0603FR-074K7L | Yageo | 5 | 100 | [LCSC C99782](https://www.lcsc.com/product-detail/C99782.html) | 0.0034 | 0.34 | in stock |
| RC0603FR-075K1L | Yageo | 2 | 100 | [LCSC C105580](https://www.lcsc.com/product-detail/C105580.html) | 0.0023 | 0.23 | in stock |
| RC0603JR-070RL | Yageo | 3 | 100 | [LCSC C95177](https://www.lcsc.com/product-detail/C95177.html) | 0.0024 | 0.24 | in stock |
| RC0805FR-07120RL | Yageo | 1 | 100 | [LCSC C114245](https://www.lcsc.com/product-detail/C114245.html) | 0.0069 | 0.69 | in stock |
| RC0805FR-072R2L | Yageo | 1 | 50 | [LCSC C137549](https://www.lcsc.com/product-detail/C137549.html) | 0.0121 | 0.61 | in stock |
| RC1206FR-0710KL | Yageo | 1 | 50 | [LCSC C132649](https://www.lcsc.com/product-detail/C132649.html) | 0.0096 | 0.48 | in stock |
| REF2025AIDDCR | Texas Instruments | 2 | 2 | [LCSC C962078](https://www.lcsc.com/product-detail/C962078.html) | 1.8258 | 3.65 | in stock |
| RT0603BRD07100KL | Yageo | 11 | 20 | [LCSC C122538](https://www.lcsc.com/product-detail/C122538.html) | 0.0325 | 0.65 | in stock |
| RT0603BRD0710KL | Yageo | 17 | 20 | [LCSC C95204](https://www.lcsc.com/product-detail/C95204.html) | 0.0331 | 0.66 | in stock |
| RT0603BRD0715KL | Yageo | 1 | 20 | [LCSC C326733](https://www.lcsc.com/product-detail/C326733.html) | 0.0351 | 0.70 | in stock |
| RT0603BRD0716K9L | Yageo | 1 | 20 | [LCSC C861156](https://www.lcsc.com/product-detail/C861156.html) | 0.036 | 0.72 | in stock |
| RT0603BRD07324KL | Yageo | 1 | 20 | [LCSC C861321](https://www.lcsc.com/product-detail/C861321.html) | 0.0346 | 0.69 | in stock |
| RT0603BRD0740K2L | Yageo | 1 | 10 | [LCSC C723489](https://www.lcsc.com/product-detail/C723489.html) | 0.0604 | 0.60 | in stock |
| RT0603BRD0751K1L | Yageo | 1 | 20 | [LCSC C861457](https://www.lcsc.com/product-detail/C861457.html) | 0.0403 | 0.81 | in stock |
| RT0603BRD078K45L | Yageo | 1 | 20 | [LCSC C861590](https://www.lcsc.com/product-detail/C861590.html) | 0.0403 | 0.81 | in stock |
| RT0603BRD0790K9L | Yageo | 2 | 20 | [LCSC C728600](https://www.lcsc.com/product-detail/C728600.html) | 0.0434 | 0.87 | in stock |
| SMCJ30A | Littelfuse | 1 | 5 | [LCSC C224048](https://www.lcsc.com/product-detail/C224048.html) | 0.2982 | 1.49 | in stock |
| SN74LVC1G11DBVR | Texas Instruments | 6 | 10 | [LCSC C22046](https://www.lcsc.com/product-detail/C22046.html) | 0.2213 | 2.21 | in stock |
| SN74LVC1G14DBVR | Texas Instruments | 1 | 10 | [LCSC C7835](https://www.lcsc.com/product-detail/C7835.html) | 0.0604 | 0.60 | in stock |
| SN74LVC1G17DBVR | Texas Instruments | 1 | 1 | [Mouser 595-SN74LVC1G17DBVR](https://www.mouser.com/en/ProductDetail/Texas-Instruments/SN74LVC1G17DBVR?qs=fvkeCqCHl3BQIcdbAa1fbQ%3D%3D) | 0.15 | 0.15 | in stock |
| SN74LVC1G74DCTR | Texas Instruments | 2 | 2 | [LCSC C840104](https://www.lcsc.com/product-detail/C840104.html) | 0.8392 | 1.68 | in stock |
| SN74LVC244APWR | Texas Instruments | 1 | 5 | [LCSC C7668](https://www.lcsc.com/product-detail/C7668.html) | 0.3026 | 1.51 | in stock |
| SN74LVC3G17DCTR | Texas Instruments | 3 | 3 | [LCSC C18213](https://www.lcsc.com/product-detail/C18213.html) | 0.7613 | 2.28 | in stock |
| STM32G474VET6 | STMicroelectronics | 1 | 1 | [LCSC partner offer C431632](https://www.lcsc.com/product-detail/C431632.html) | 16.2415 | 16.24 | cart marks backordered; partner advertises 3 units and 7-9 business days; confirmation required |
| STPS5H100AF | STMicroelectronics | 1 | 1 | [LCSC C2802050](https://www.lcsc.com/product-detail/C2802050.html) | 0.64 | 0.64 | in stock |
| TCAN3403DRQ1 | Texas Instruments | 1 | 1 | [Mouser 595-TCAN3403DRQ1](https://www.mouser.com/en/ProductDetail/Texas-Instruments/TCAN3403DRQ1?qs=VVKQmw408U8i3BeOClYB9g%3D%3D) | 1.77 | 1.77 | backordered; delivery not confirmed |
| TL3342F160QG | E-Switch | 2 | 2 | [LCSC C2886898](https://www.lcsc.com/product-detail/C2886898.html) | 1.0456 | 2.09 | in stock |
| TLV3011BIDBVR | Texas Instruments | 1 | 1 | [LCSC C20345920](https://www.lcsc.com/product-detail/C20345920.html) | 3.1482 | 3.15 | in stock |
| TLV3201AIDBVR | Texas Instruments | 1 | 1 | [LCSC C105188](https://www.lcsc.com/product-detail/C105188.html) | 0.98 | 0.98 | in stock |
| TLV75801PDRVR | Texas Instruments | 1 | 5 | [LCSC C2876308](https://www.lcsc.com/product-detail/C2876308.html) | 0.345 | 1.73 | in stock |
| TLV9024PWR | Texas Instruments | 2 | 2 | [Mouser 595-TLV9024PWR](https://www.mouser.com/en/ProductDetail/Texas-Instruments/TLV9024PWR?qs=QNEnbhJQKvaHPXXeMhKu8Q%3D%3D) | 1.84 | 3.68 | backordered; delivery not confirmed |
| TLV9062IDR | Texas Instruments | 2 | 5 | [LCSC C398355](https://www.lcsc.com/product-detail/C398355.html) | 0.1221 | 0.61 | in stock |
| TLV9064IPWR | Texas Instruments | 1 | 5 | [LCSC C779410](https://www.lcsc.com/product-detail/C779410.html) | 0.3927 | 1.96 | in stock |
| TPS2116DRLR | Texas Instruments | 1 | 1 | [LCSC C3235557](https://www.lcsc.com/product-detail/C3235557.html) | 0.40 | 0.40 | in stock |
| TPS2553DBVR-1 | Texas Instruments | 2 | 5 | [LCSC C111738](https://www.lcsc.com/product-detail/C111738.html) | 0.2952 | 1.48 | in stock |
| TPS3431SDRBR | Texas Instruments | 1 | 1 | [Mouser 595-TPS3431SDRBR](https://www.mouser.com/en/ProductDetail/Texas-Instruments/TPS3431SDRBR?qs=w%2Fv1CP2dgqr73oCnz11srA%3D%3D) | 2.07 | 2.07 | backordered; delivery not confirmed |
| TPS3808G50DBVR | Texas Instruments | 1 | 1 | [LCSC C134123](https://www.lcsc.com/product-detail/C134123.html) | 1.1756 | 1.18 | in stock |
| TPS389033DSER | Texas Instruments | 1 | 1 | [LCSC C702227](https://www.lcsc.com/product-detail/C702227.html) | 1.95 | 1.95 | in stock |
| UCC27511ADBVR | Texas Instruments | 1 | 5 | [LCSC C2676982](https://www.lcsc.com/product-detail/C2676982.html) | 0.386 | 1.93 | in stock |
| USB4105-GF-A | GCT | 1 | 1 | [Mouser 640-USB4105-GF-A](https://www.mouser.com/en/ProductDetail/GCT/USB4105-GF-A?qs=KUoIvG%2F9IlY%2FMLlBMpStpA%3D%3D) | 0.80 | 0.80 | in stock |
| USBLC6-2SC6 | STMicroelectronics | 1 | 1 | [Mouser 511-USBLC6-2SC6](https://www.mouser.com/en/ProductDetail/STMicroelectronics/USBLC6-2SC6?qs=po45yt2pPpu%2FhNIlwQdTlg%3D%3D) | 0.59 | 0.59 | in stock |
| WSLP25123L000FEA | Vishay | 1 | 1 | [Mouser 71-WSLP25123L000FEA](https://www.mouser.com/en/ProductDetail/Vishay/WSLP25123L000FEA?qs=2spUtbtSOvg%252BTTBA6ckz0A%3D%3D) | 1.42 | 1.42 | backordered; delivery not confirmed |
| XT60PW-M | AMASS | 1 | 1 | [TME XT60PW-M](https://www.tme.eu/en/details/xt60pw-m/dc-power-connectors/amass/) | 1.053 | 1.05 | international listing 726 in stock; US storefront error; US quote not confirmed |

References for each part are in [purchasing-draft.csv](purchasing-draft.csv).
