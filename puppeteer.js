const puppeteer = require('puppeteer');
const fs = require('fs');

// 简单的参数验证（文档建议的健壮性处理）
if (process.argv.length < 4) {
    console.error('参数错误：需要URL和输出路径');
    process.exit(1);
}

const [url, outputPath] = process.argv.slice(2);

async function captureScreenshot() {
    let browser = null;
    try {
        // 启动浏览器（添加必要的参数）
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ],
            timeout: 30000
        });

        const page = await browser.newPage();
        
        // 设置合理的视口大小
        await page.setViewport({ width: 1200, height: 900 });
        
        // 导航到目标页面
        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 30000
        });
        
        // 等待卡组内容加载完成（根据实际页面调整）
        await page.waitForSelector('.deck-builder', { timeout: 15000 });
        
        // 等待图片加载
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 截取卡组区域
        await page.screenshot({
            path: outputPath,
            clip: { x: 50, y: 100, width: 1100, height: 700 }
        });
        
        console.log('截图成功');
        process.exit(0);
        
    } catch (error) {
        console.error('截图失败:', error.message);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close().catch(() => {});
        }
    }
}

// 执行截图
captureScreenshot();
    