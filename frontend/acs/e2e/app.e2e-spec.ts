import {AcsPage} from './app.po';

describe('acs App', () => {
    let page: AcsPage;

    beforeEach(() => {
        page = new AcsPage();
    });

    it('should display message saying app works', () => {
        page.navigateTo();
        expect(page.getParagraphText()).toEqual('app works!');
    });
});
