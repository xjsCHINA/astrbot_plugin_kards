const puppeteer = require('puppeteer');
const fs = require('fs');

// 从命令行获取参数
const [url, outputPath] = process.argv.slice(2);

if (!url || !outputPath) {
    console.error('缺少参数: 需要URL和输出文件路径');
    process.exit(1);
}

async function takeScreenshot() {
    let browser;
    try {
        // 启动浏览器
        browser = await puppeteer.launch({
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ],
            timeout: 60000
        });

        // 创建页面
        const page = await browser.newPage();
        await page.setViewport({ width: 1200, height: 1000 });
        
        // 导航到目标页面
        await page.goto(url, {
            waitUntil: 'networkidle2',
            timeout: 60000
        });
        
        // 等待卡组加载完成（根据实际页面调整选择器）
        await page.waitForSelector('.deck-content', { timeout: 30000 });
        await new Promise(resolve => setTimeout(resolve, 3000)); // 额外等待
        
        // 截取卡组区域
        const deckElement = await page.$('.deck-content');
        if (deckElement) {
            await deckElement.screenshot({ path: outputPath });
        } else {
            // 备选方案：截取整个页面
            await page.screenshot({ path: outputPath, fullPage: true });
        }
        
        // 验证截图
        if (fs.existsSync(outputPath) && fs.statSync(outputPath).size > 0) {
            console.log('截图成功');
            process.exit(0);
        } else {
            console.error('截图文件无效');
            process.exit(1);
        }
        
    } catch (error) {
        console.error('截图失败:', error.message);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close().catch(err => console.error('关闭浏览器失败:', err));
        }
    }
}

takeScreenshot();
    