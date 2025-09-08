const puppeteer = require('puppeteer');
const fs = require('fs');

// 从命令行参数获取URL和输出文件路径
const [url, outputPath] = process.argv.slice(2);

if (!url || !outputPath) {
    console.error('缺少参数：需要URL和输出文件路径');
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
                '--disable-gpu',
                '--remote-debugging-port=9222'
            ],
            timeout: 60000
        });

        // 创建新页面
        const page = await browser.newPage();
        
        // 设置用户代理，模拟真实浏览器
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36');
        
        // 设置页面大小
        await page.setViewport({ width: 1200, height: 1000 });
        
        // 导航到目标URL
        console.log(`导航到: ${url}`);
        await page.goto(url, { 
            waitUntil: 'networkidle2',
            timeout: 60000
        });
        
        // 等待页面加载完成 - 调整选择器以匹配实际页面结构
        console.log('等待卡组加载...');
        await page.waitForSelector('.deck-content', { timeout: 30000 });
        
        // 等待额外时间确保所有图片加载完成
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        // 尝试找到卡组容器元素
        const deckElement = await page.$('.deck-content');
        if (!deckElement) {
            console.error('未找到卡组内容元素');
            // 作为备选，截取整个页面
            await page.screenshot({ path: outputPath, fullPage: true });
            console.log('已截取整个页面作为备选');
        } else {
            // 只截取卡组区域
            await deckElement.screenshot({ path: outputPath });
            console.log('已截取卡组区域');
        }
        
        // 验证文件是否创建
        if (fs.existsSync(outputPath) && fs.statSync(outputPath).size > 0) {
            console.log('截图成功');
            process.exit(0);
        } else {
            console.error('截图文件未生成或为空');
            process.exit(1);
        }
        
    } catch (error) {
        console.error('截图过程出错:', error.message);
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close().catch(err => console.error('关闭浏览器时出错:', err));
        }
    }
}

// 执行截图
takeScreenshot();
    